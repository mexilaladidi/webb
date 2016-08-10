#!/bin/sh
sudo apt-get -y install pptpd
sudo sed -i '/client/a\lalala pptpd "1212123" * ' /etc/ppp/chap-secrets
sudo sed -i '/localip 192.168.0.1/a\localip 192.168.0.1' /etc/pptpd.conf
sudo sed -i '/remoteip 192.168.0.234-238,192.168.0.245/a\remoteip 192.168.0.234-238,192.168.0.245' /etc/pptpd.conf
sudo sed -i '/#ms-dns 10.0.0.1/a\ms-dns 8.8.8.8' /etc/ppp/pptpd-options
sudo sed -i '/ms-dns 8.8.8.8/a\ms-dns 8.8.4.4' /etc/ppp/pptpd-options
sudo sed -i '/net.ipv4.ip_forward=1/a\net.ipv4.ip_forward=1' /etc/sysctl.conf
sudo sysctl -p
sudo iptables -t nat -A POSTROUTING -s 192.168.0.0/24 -o eth0 -j MASQUERADE
sudo service pptpd restart
