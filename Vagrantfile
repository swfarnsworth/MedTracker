# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.network "forwarded_port", guest: 4040, host: 8080
  config.vm.network "private_network", type: "dhcp"

config.vm.provider "virtualbox" do |v|
  v.name = "med_tracker_box"
  v.gui = false
  v.memory = 2000
  v.cpus = 1
end

config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python3 python3-pip python3-dev mssql-server
    # Require older version of pip to install flask-ask
    python -m pip install pip==9.0.3
    pip3 install -r /vagrant/requirements.txt
SHELL
end