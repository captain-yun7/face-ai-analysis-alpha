# 데이터 소스 - Availability Domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# 데이터 소스 - Ubuntu Images for ARM
data "oci_core_images" "ubuntu_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

  filter {
    name   = "display_name"
    values = [".*aarch64.*"]
    regex  = true
  }
}

# ARM A1 인스턴스
resource "oci_core_instance" "face_api_instance" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = var.instance_display_name
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }

  create_vnic_details {
    subnet_id                 = oci_core_subnet.face_api_subnet.id
    display_name              = "face-api-vnic"
    assign_public_ip          = true
    hostname_label            = "faceapi"
    assign_private_dns_record = true
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu_images.images[0].id
    boot_volume_size_in_gbs = 50
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      ssh_public_key = var.ssh_public_key
    }))
  }

  freeform_tags = {
    "Project"      = "face-api"
    "Environment"  = "production"
    "Architecture" = "ARM64"
  }

  preserve_boot_volume = false
}

# 추가 블록 볼륨 (프리티어 200GB 활용)
resource "oci_core_volume" "face_api_volume" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "face-api-storage"
  size_in_gbs         = 50

  freeform_tags = {
    "Project" = "face-api"
  }
}

# 볼륨 첨부
resource "oci_core_volume_attachment" "face_api_volume_attachment" {
  attachment_type = "iscsi"
  instance_id     = oci_core_instance.face_api_instance.id
  volume_id       = oci_core_volume.face_api_volume.id
  display_name    = "face-api-volume-attachment"
}