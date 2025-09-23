# VCN 생성
resource "oci_core_vcn" "face_api_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = var.vcn_cidr_blocks
  display_name   = "face-api-vcn"
  dns_label      = "faceapi"

  freeform_tags = {
    "Project"     = "face-api"
    "Environment" = "production"
  }
}

# 인터넷 게이트웨이
resource "oci_core_internet_gateway" "face_api_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-igw"
  enabled        = true

  freeform_tags = {
    "Project" = "face-api"
  }
}

# 라우트 테이블
resource "oci_core_route_table" "face_api_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.face_api_igw.id
  }

  freeform_tags = {
    "Project" = "face-api"
  }
}

# 서브넷
resource "oci_core_subnet" "face_api_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.face_api_vcn.id
  cidr_block        = var.subnet_cidr_block
  display_name      = "face-api-subnet"
  dns_label         = "faceapisub"
  route_table_id    = oci_core_route_table.face_api_rt.id
  security_list_ids = [oci_core_security_list.face_api_sl.id]

  freeform_tags = {
    "Project" = "face-api"
  }
}

# 보안 그룹
resource "oci_core_security_list" "face_api_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.face_api_vcn.id
  display_name   = "face-api-sl"

  # 아웃바운드 규칙 (모든 트래픽 허용)
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # 인바운드 규칙 - SSH
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6" # TCP
    tcp_options {
      min = 22
      max = 22
    }
    description = "SSH access"
  }

  # 인바운드 규칙 - HTTP
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6" # TCP
    tcp_options {
      min = 80
      max = 80
    }
    description = "HTTP access"
  }

  # 인바운드 규칙 - HTTPS
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6" # TCP
    tcp_options {
      min = 443
      max = 443
    }
    description = "HTTPS access"
  }

  # ICMP 규칙 (ping)
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "1" # ICMP
    icmp_options {
      type = 3
      code = 4
    }
    description = "ICMP Path Discovery"
  }

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "1" # ICMP
    icmp_options {
      type = 3
    }
    description = "ICMP Destination Unreachable"
  }

  freeform_tags = {
    "Project" = "face-api"
  }
}