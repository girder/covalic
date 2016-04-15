#!/bin/bash
# argv:
# $1: pod name
# $2: path to covalic_admin.pem
ansible-playbook -i plugins/inventory/ec2.py -e pod=$1 \
    -t rewire --vault-password-file vault-password.txt --private-key=$2 \
    -e ansible_ssh_private_key_file=$2 -e ansible_ssh_user=ubuntu provision.yml
