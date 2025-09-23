output "instance_id" {
  description = "OCID of the created instance"
  value       = oci_core_instance.face_api_instance.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = oci_core_instance.face_api_instance.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = oci_core_instance.face_api_instance.private_ip
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/oracle_key ubuntu@${oci_core_instance.face_api_instance.public_ip}"
}

output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.face_api_vcn.id
}

output "subnet_id" {
  description = "OCID of the subnet"
  value       = oci_core_subnet.face_api_subnet.id
}

output "volume_id" {
  description = "OCID of the additional storage volume"
  value       = oci_core_volume.face_api_volume.id
}