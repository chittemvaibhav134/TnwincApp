from locust import HttpLocust, TaskSet, between, task
import os

class StuffToDo(TaskSet):
    client_id = 'admin-api-proxy'
    secret = os.environ['AdminApiProxySecret']
    def get_token(self):
        endpoint = '/auth/realms/master/protocol/openid-connect/token'
        payload = "grant_type=client_credentials"
        data = bytes(payload.encode('utf-8'))
        r = self.client.post(
            endpoint, 
            headers={'Content-Type' : 'application/x-www-form-urlencoded'},
            auth=(self.client_id, self.secret),
            data=data
        )
        token = r.json()
        self.refresh_token = token['refresh_token']
        self.client.headers.update({"Authorization": f"Bearer {token['access_token']}"})
        
    def on_start(self):
        self.get_token( )

    @task(2)    
    def get_realms(self):
        endpoint = "/auth/admin/realms"
        self.client.get(endpoint)

    @task(2) 
    def get_clients(self):
        endpoint = "/auth/admin/realms/navex/clients"
        self.client.get(endpoint)

    @task(1)
    def refresh_that_token(self):
        endpoint = '/auth/realms/master/protocol/openid-connect/token'
        payload = f"refresh_token={self.refresh_token}&client_id={self.client_id}&grant_type=refresh_token"
        data = bytes(payload.encode('utf-8'))
        headers = {'Content-Type' : 'application/x-www-form-urlencoded', "Authorization": self.client.headers['Authorization']}
        r = self.client.post(
            endpoint, 
            headers=headers,
            data=data,
            auth=(self.client_id, self.secret)
        )
        token = r.json()
        self.refresh_token = token['refresh_token']
        self.client.headers.update({"Authorization": f"Bearer {token['access_token']}"})
        del(self.client.cookies['AWSALBCORS'])
        del(self.client.cookies['AWSALB'])

class NormalUsage(HttpLocust):
    task_set = StuffToDo
    wait_time = between(1, 5)


### Usage ###
"""
pip install locust
$env:AdminApiProxySecret = '<locate current admin-api-proxy secret in ssm>'
# no web ui
locust -f locustfile.py --no-web --host 'https://id3.psychic-potato.navex-int.com' -c 100 -r 5 --stop-timeout 5 --run-time 5m
# with web ui
locust -f locustfile.py --host 'https://id3.psychic-potato.navex-int.com'
"""