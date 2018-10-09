Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-18.04"
  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 2
    # Prevent 'xenial-16.04-cloudimg-console.log' from being created
    v.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
  end

  config.vm.synced_folder ".", "/vagrant"
  config.vm.synced_folder ".", "/home/vagrant/covalic"

  config.vm.network "forwarded_port", guest: 8080, host: 8080, auto_correct: true
  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "ansible/vagrant.yml"
  end
end
