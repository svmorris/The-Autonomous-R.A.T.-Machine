FROM kali-last-release

RUN apt update
# RUN apt install kali-linux-headless -y
RUN touch /stop-flag


# Recon tools
RUN apt-get install nmap -y
RUN apt-get install arp-scan -y
RUN apt-get install dnsrecon -y
RUN apt-get install net-tools -y
RUN apt-get install iputils-ping -y

# Vuln scanning tools
RUN apt-get install nikto -y
RUN apt-get install metasploit-framework -y


# if the stop-flag file is deleted from root then the container should stop automatically
# This should make stopping the system slightly easier than having to run the kill command
CMD while [ -f /stop-flag ]; do sleep 2; done
