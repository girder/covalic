#!/bin/bash
# argv:
# $1: pod name
# $2: path to covalic_admin.pem
ansible-playbook -i plugins/inventory/ec2.py build_pod_inventory.yml -e pod=$1 -e path_to_covalic_admin_key=$2 --private-key=$2
