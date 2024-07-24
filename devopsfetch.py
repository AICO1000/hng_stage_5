import argparse
import psutil
import docker
import subprocess
import logging
import pwd
import os
from datetime import datetime

def setup_logging():
    logging.basicConfig(filename='/var/log/devopsfetch.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    logging.info('devopsfetch started')

def get_ports():
    ports = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port not in [c['port'] for c in ports]:
            ports.append({'port': conn.laddr.port, 'status': conn.status})
    return ports

def get_docker_info():
    client = docker.from_env()
    images = client.images.list()
    containers = client.containers.list(all=True)
    return images, containers

def get_nginx_domains():
    config_files = [f for f in os.listdir('/etc/nginx/sites-enabled') if f.endswith('.conf')]
    domains = []
    for file in config_files:
        with open(f'/etc/nginx/sites-enabled/{file}', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'server_name' in line:
                    domains.append(line.split()[1])
    return domains

def get_users():
    users = []
    for user in pwd.getpwall():
        try:
            last_login = subprocess.check_output(['last', '-1', user.pw_name]).decode('utf-8').split('\n')[0]
            users.append({'username': user.pw_name, 'last_login': last_login})
        except:
            users.append({'username': user.pw_name, 'last_login': 'Never logged in'})
    return users

def get_time_range(start, end):
    logs = []
    with open('/var/log/devopsfetch.log', 'r') as f:
        for line in f:
            log_time = datetime.strptime(line.split(' - ')[0], '%Y-%m-%d %H:%M:%S,%f')
            if start <= log_time <= end:
                logs.append(line)
    return logs

def main():
    parser = argparse.ArgumentParser(description='devopsfetch - A tool for server information retrieval and monitoring')
    parser.add_argument('-p', '--port', type=int, help='Display all active ports and services or details of a specific port')
    parser.add_argument('-d', '--docker', type=str, help='List all Docker images and containers or details of a specific container')
    parser.add_argument('-n', '--nginx', type=str, help='Display all Nginx domains and their ports or details of a specific domain')
    parser.add_argument('-u', '--users', type=str, help='List all users and their last login times or details of a specific user')
    parser.add_argument('-t', '--time', nargs='+', help='Display activities within a specified time range')
    parser.add_argument('-l', '--log', action='store_true', help='Enable logging')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')

    args = parser.parse_args()

    if args.log:
        setup_logging()

    if args.port is not None:
        if isinstance(args.port, int):
            ports = get_ports()
            if args.port in [p['port'] for p in ports]:
                print(f'Port {args.port} is active')
            else:
                print(f'Port {args.port} is not active')
        else:
            for port in get_ports():
                print(f"Port: {port['port']}, Status: {port['status']}")

    if args.docker is not None:
        images, containers = get_docker_info()
        if args.docker:
            container = [c for c in containers if c.name == args.docker]
            if container:
                print(container[0].attrs)
            else:
                print(f'No container with name {args.docker}')
        else:
            for image in images:
                print(image.tags)
            for container in containers:
                print(container.name)

    if args.nginx is not None:
        domains = get_nginx_domains()
        if args.nginx:
            if args.nginx in domains:
                with open(f'/etc/nginx/sites-enabled/{args.nginx}.conf', 'r') as f:
                    print(f.read())
            else:
                print(f'No domain with name {args.nginx}')
        else:
            for domain in domains:
                print(domain)

    if args.users is not None:
        users = get_users()
        if args.users:
            user = [u for u in users if u['username'] == args.users]
            if user:
                print(user[0])
            else:
                print(f'No user with name {args.users}')
        else:
            for user in users:
                print(f"User: {user['username']}, Last Login: {user['last_login']}")

    if args.time:
        if len(args.time) == 2:
            start = datetime.strptime(args.time[0], '%Y-%m-%d')
            end = datetime.strptime(args.time[1], '%Y-%m-%d')
        else:
            start = datetime.strptime(args.time[0], '%Y-%m-%d')
            end = datetime.now()
        logs = get_time_range(start, end)
        for log in logs:
            print(log)

if __name__ == '__main__':
    main()
