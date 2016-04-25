#!/bin/bash
# argv:
# $1: pod name
# $2: path to covalic_admin.pem
if [ "$#" -ne 2 ]; then
  echo "Usage: provision.sh <pod> <path_to_covalic_admin.pem>"
  exit 1
fi

ansible-playbook -i plugins/inventory/ec2.py -e pod=$1 \
    --vault-password-file vault-password.txt --private-key=$2 \
    -e ansible_ssh_private_key_file=$2 -e ansible_ssh_user=ubuntu provision.yml
