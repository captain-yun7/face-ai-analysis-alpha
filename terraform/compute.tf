# 데이터 소스 - Availability Domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# 데이터 소스 - Ubuntu Images for ARM
data "oci_core_images" "ubuntu_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"

}

# ARM A1 인스턴스
resource "oci_core_instance" "face_api_instance" {
  availability_domain = try(data.oci_identity_availability_domains.ads.availability_domains[0].name, "IVaY:AP-CHUNCHEON-1-AD-1")
  compartment_id      = var.compartment_ocid
  display_name        = var.instance_display_name
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
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
    source_id               = try(data.oci_core_images.ubuntu_images.images[0].id, "ocid1.image.oc1.ap-chuncheon-1.aaaaaaaa4pfzhxsrwmjb6nnixq5k5f6k2n2k75u3fzs6h4rpbrfpzf4t66vq")
    boot_volume_size_in_gbs = 50
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }

  freeform_tags = {
    "Project"      = "face-api"
    "Environment"  = "production"
    "Architecture" = "ARM64"
  }

  preserve_boot_volume = false
}