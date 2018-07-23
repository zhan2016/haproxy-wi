#!/usr/bin/env python3
import subprocess
import time
import argparse
import os, sys
sys.path.append(os.path.join(sys.path[0], '../'))
import funct
import sql
import signal

class GracefulKiller:
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)
	
	def exit_gracefully(self,signum, frame):
		self.kill_now = True

def main():
	servers = sql.select_alert()
	started_workers = get_worker()
	servers_list = []
	
	for serv in servers:
		servers_list.append(serv[0])
			
	need_kill=list(set(started_workers) - set(servers_list))
	need_start=list(set(servers_list) - set(started_workers))
	
	if need_kill:
		for serv in need_kill:
			kill_worker(serv)
			
	if need_start:
		for serv in need_start:
			start_worker(serv)
	
def start_worker(serv):
	cmd = "tools/checker_worker.py %s &" % serv
	os.system(cmd)
	funct.logging("localhost", " Start new worker for: "+serv, alerting=1)
	
def kill_worker(serv):
	cmd = "ps ax |grep 'tools/checker_worker.py %s'|grep -v grep |awk '{print $1}' |xargs kill" % serv
	output, stderr = funct.subprocess_execute(cmd)
	funct.logging("localhost", " Kill worker for: "+serv, alerting=1)
	if stderr:
		funct.logging("localhost", stderr, alerting=1)

def kill_all_workers():
	cmd = "ps ax |grep 'tools/checker_worker.py' |grep -v grep |awk '{print $1}' |xargs kill"
	output, stderr = funct.subprocess_execute(cmd)
	funct.logging("localhost", " Killed all workers", alerting=1)
	if stderr:
		funct.logging("localhost", stderr, alerting=1)
		
def get_worker():
	cmd = "ps ax |grep 'tools/checker_worker.py' |grep -v grep |awk '{print $7}'"
	output, stderr = funct.subprocess_execute(cmd)
	if stderr:
		funct.logging("localhost", stderr, alerting=1)
	return output
	
if __name__ == "__main__":
	funct.logging("localhost", " Master started", alerting=1)
	killer = GracefulKiller()
	
	while True:
		main()
		time.sleep(30)
		
		if killer.kill_now:
			break
			
	kill_all_workers()
	funct.logging("localhost", " Master shutdown", alerting=1)