#!/bin/bash
# argv:
# $1: pod name
ansible-playbook -i inventory/local create.yml -e pod=$1
