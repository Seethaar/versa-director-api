#!/usr/bin/env python3
import requests, json, os, yaml, base64, hashlib, datetime, tempfile, logging
from pathlib import Path
from cryptography.fernet import Fernet
from getpass import getpass

class DirectorAccess:
  '''
  This is a simple class object representing a typical Versa Director API access handle
  with all necessary variables embedded. This is used to structure the API calls and also
  to enable code reusablility

  :Class Variables: None
  '''
  def __init__(self,config_file):
    '''
    Constructor Class

    :Inputs: Director's hostname -> String, REST API Port & Auth Port for Token Management -> Integer
    '''
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    if not os.environ.get('V_TENANCY'):
      self.tenancy = input("please enter the tenancy name : ")
    else:
      self.tenancy = os.environ.get('V_TENANCY')
    if not os.environ.get('V_REGION'):
      region_input = ""
      while region_input not in ['APAC', 'EMEA', 'US']:
        region_input = input("please select the region from values APAC, EMEA or US : ")
      self.region = region_input
    else:
      self.region = os.environ.get('V_REGION')
    if not os.environ.get('V_API_CSECRET'):
      self.api_client_secret = getpass("please input Versa supplied Oauth API Client Secret : ")
      logging.info('Just in case you are wondering, your input for API secret was collected. Thanks.')
    else:
      self.api_client_secret = os.environ.get('V_API_CSECRET')
    if not os.environ.get('V_USER'):
      self.username = input("please input the versa director username : ")
    else:
      self.username = os.environ.get('V_USER')
      logging.info(f'The versa director username {self.username} was chosen by this program. Thanks.')
    if not os.environ.get('V_PASS'):
      self.password = getpass("please input the versa director password : ")
      logging.info('Just in case you are wondering, your input for versa director was collected. Thanks.')
    else:
      self.password = os.environ.get('V_PASS')
    with open(config_file,'r') as fh:
      director_data = yaml.safe_load(fh)
    config_search_key = '_'.join([self.region, self.tenancy])
    this_director = director_data[config_search_key]
    logging.info(f"You have selected Versa {self.tenancy} headend and {self.region} tenancy.\n")
    self.director_url = this_director['url']
    self.rest_api_port = str(this_director['rest_api_port'])
    self.api_client_id = this_director['api_client_id']

  @staticmethod
  def store_tokens(username,password,access_token,refresh_token,region,tenancy):
    '''
    Static Method to encrypt and store access and refresh tokens derived from Versa Auth API

    :Inputs: Access and Refresh Tokens -> String
    :Outputs: None
    :Store: Byte-Code File in temp directory
    '''
    key = password.encode(encoding='utf-8')
    key2 = hashlib.md5(key).hexdigest()
    key_64= base64.urlsafe_b64encode(key2.encode())
    fernet = Fernet(key_64)
    datapath = Path(tempfile.gettempdir() + f'/{region}_{tenancy}_{username}')
    if os.path.exists(datapath):
      os.remove(datapath)
    with open(datapath,'wb') as fh:
      fh.write(fernet.encrypt(access_token.encode()))
      fh.write(b'\n')
      fh.write(fernet.encrypt(refresh_token.encode()))
      fh.write(b'\n')
      fh.write(fernet.encrypt(str(datetime.datetime.today().date()).encode()))

  @staticmethod
  def read_tokens(username,password,region,tenancy):
    '''
    Static Method to retrieve and decrypt access and refresh tokens derived from Versa Auth API

    :Inputs: Versa Organisational User Password -> String
    :Outputs: Access and Refresh Tokens -> String
    :Store: Byte-Code File in temp directory
    '''
    key = password.encode(encoding='utf-8')
    key2 = hashlib.md5(key).hexdigest()
    key_64= base64.urlsafe_b64encode(key2.encode())
    fernet = Fernet(key_64)
    datapath = Path(tempfile.gettempdir() + f'/{region}_{tenancy}_{username}')
    with open(datapath,'rb') as fh:
      enc_content = [line.rstrip() for line in fh]
      access_token = fernet.decrypt(enc_content[0]).decode()
      refresh_token = fernet.decrypt(enc_content[1]).decode()
      token_date = fernet.decrypt(enc_content[2]).decode()
    return access_token, refresh_token, token_date

  @staticmethod
  def delete_tokens(username,region,tenancy):
    datapath = Path(tempfile.gettempdir() + f'/{region}_{tenancy}_{username}')
    os.remove(datapath)
    logging.info(f'\nToken file {datapath} deleted.\n')
    

  def generate_token(self):
    '''
    Method to validate stored tokens or derive from Versa Auth API, if they are invalid or unavailable.

    :Inputs: None
    :Outputs: Access and Refresh Tokens -> String
    :Store: Byte-Code File in temp directory
    '''   
    token_validity = 0
    datapath = Path(tempfile.gettempdir() + f'/{self.region}_{self.tenancy}_{self.username}')
    if os.path.exists(datapath):
      self.access_token, self.refresh_token, self.token_date = DirectorAccess.read_tokens(self.username,self.password,self.region,self.tenancy)
      # VALIDATING ACCESS & REFRESH TOKENS STORED IN THE ENVIRONMENT VARIABLES
      if self.token_date == str(datetime.datetime.today().date()):
        try:
          headers = {'Accept': 'application/json','Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
          response = requests.get(f'{self.director_url}:{self.rest_api_port}/vnms/organization/orgs', headers=headers)
          if response.status_code == 200:
            logging.info('Existing Access Token is still valid ..\n')
            token_validity = 1
          else:
            response.raise_for_status()
        except:
          # SEEKING REFRESHED ACCESS & REFRESH TOKENS FROM VD API
          payload = json.dumps({
                      "grant_type": "refresh_token",
                      "client_id": self.api_client_id,
                      "client_secret": self.api_client_secret,
                      "refresh_token": f'{self.refresh_token}'
                    })
          headers = {'Accept': 'application/json','Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
          # response = requests.post(f'{self.director_url}:{self.auth_token_port}/auth/refresh', headers=headers, data=payload)
          response = requests.post(f'{self.director_url}:{self.rest_api_port}/auth/refresh', headers=headers, data=payload)
          if response.status_code == 200:
            logging.info(f"Just refreshed the Access Token at {response.json()['issued_at']}\n")
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
            DirectorAccess.store_tokens(self.username,self.password, self.access_token, self.refresh_token,self.region,self.tenancy)
            # os.environ['V_ACCESS_TOKEN'] = self.access_token
            # os.environ['V_REFRESH_TOKEN'] = self.refresh_token
            return self.region, self.tenancy, self.access_token, self.refresh_token
          elif response.status_code == 401:
            logging.info('We suspect the session tokens were invalidated by Versa API Gateway. I shall delete the tokens now and you may retry later.\n')
            DirectorAccess.delete_tokens(self.username,self.region,self.tenancy)
          else:
            response.raise_for_status()     
        else:
          return self.region, self.tenancy, self.access_token, self.refresh_token   
      else:
        token_validity = 0
        os.remove(datapath)
    if token_validity == 0:
      # SEEKING NEW ACCESS & REFRESH TOKENS FROM VD AUTH API
#       encoded_auth_string =  base64.b64encode((f'{self.username}:{self.password}').encode()).decode()
#       headers = {'Accept': 'application/json','Content-Type': 'application/json', 'Authorization': f'Basic {encoded_auth_string}'}
      headers = {'Accept': 'application/json','Content-Type': 'application/json'}
      payload = json.dumps({"client_id": self.api_client_id, "client_secret": self.api_client_secret, "username": self.username, "password": self.password,"grant_type": "password" })
      response = requests.post(f'{self.director_url}:{self.rest_api_port}/auth/token', headers=headers, data=payload)
      if response.status_code == 200:
        self.access_token = response.json()["access_token"]
        self.refresh_token = response.json()["refresh_token"]
        DirectorAccess.store_tokens(self.username,self.password, self.access_token, self.refresh_token,self.region,self.tenancy)        
        logging.info('Just requested new tokens from VD API...\n')
      else:
        raise Exception(response.json()['error_description'])
      return self.region, self.tenancy, self.access_token, self.refresh_token

  def run_api_get_call(self,resource=None):
    '''
    Method to baseline all API calls to Versa Director API.

    :Inputs: resoucce path on the API endpoint -> String
    :Outputs: Response from API calls -> JSON object
    '''
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
    response = requests.get(f'{self.director_url}:{self.rest_api_port}{resource}', headers=headers)
    if not response.ok:
      response.raise_for_status()
    return response.json()


  def get_orgs(self):
    '''
    Method to collect all the Orgs listed on the Versa Director API.

    :Inputs: None
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call('/vnms/organization/orgs')

  def get_device_group(self,device_group_name=None):
    '''
    Method to collect all the Orgs listed on the Versa Director API.

    :Inputs: None
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call(f'/nextgen/deviceGroup/{device_group_name}')    

  def get_device_config(self,device_name=None):
    '''
    Method to collect a device configuration listed on the Versa Director API.

    :Inputs: Name of the Device -> String
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call(f'/api/config/devices/device/{device_name}?deep=true')

  def get_list_of_device_templates(self):
    '''
    Method to collect all device templates listed on the Versa Director API.

    :Inputs: None
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call('/vnms/template/metadata/templates')

  def get_device_template(self,template_name=None):
    '''
    Method to collect a device template listed on the Versa Director API.

    :Inputs: Name of the Template -> String
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call(f'/api/config/devices/template/{template_name}?deep=true')


  ### NGFW Service Template Operations - Create, Read, Update and Delete ###
  def create_blank_ngfw_service_template(self,ngfw_st_template_name=None,tenant_org_name=None):
    '''
    Method to create a blank Service Template of type NGFW Firewall on the Versa Director API.

    :Inputs: Name of the NGFW Firewall Service Template and Tenant Org Name -> String
    :Outputs: Response -> TBD
    '''
    payload = json.dumps({
              "versanms.templateData": {
                "category": "nextgen-firewall",
                "composite_or_partial": "partial",
                "isDynamicTenantConfig": False,
                "name": f'{ngfw_st_template_name}',
                "providerTenant": f'{tenant_org_name}'}
              })
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
    response = requests.post(f'{self.director_url}:{self.rest_api_port}/vnms/template/serviceTemplate', headers=headers, data=payload)
    if response.status_code == 200:
      logging.info(f"Service Template {ngfw_st_template_name} was created in the Versa Tenancy {tenant_org_name} successfully")
      return response
    else:
      response.raise_for_status()

  def get_list_of_org_service_templates(self,tenant_org_name=None):
    '''
    Method to collect all service templates of an Tenant listed on the Versa Director API.

    :Inputs: Name of the Tenant Org -> String
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call(f'/vnms/template/metadata?organization={tenant_org_name}&type=SERVICE')

  def get_service_template(self,ngfw_st_template_name=None):
    '''
    Method to collect a service template from the Versa Director API.

    :Inputs: Name of the Service Template -> String
    :Outputs: Response from API call -> JSON object
    '''
    return self.run_api_get_call(f'/api/config/devices/template/{ngfw_st_template_name}?deep=true')
 
  def get_service_template_juniper(self,template_name=None):
    '''
    Method to collect a device template listed on the Versa Director API.

    :Inputs: Name of the Template -> String
    :Outputs: Response from API call -> JSON object
    '''
    headers = {'Accept': 'text/plain', 'Authorization': f'Bearer {self.access_token}'}
    response = requests.request("GET", f'{self.director_url}:{self.rest_api_port}/vnms/template/export?templateName={template_name}', headers=headers)
    if not response.ok:
      response.raise_for_status()
    return response.text

  def clone_service_template(self,ngfw_st_template_name=None,source_org=None,target_org=None):
    '''
    Method to clone a service template between tenancies the Versa Director API.

    :Inputs: Name of the Service Template, source Tenancy reference and target Tenancy reference -> String
    :Outputs: Response from API call -> JSON object
    '''
    payload = json.dumps({
              "versanms.templateOrgs":{
                "selectedTemplate":ngfw_st_template_name,
                "newTemplate":f'Copy_of_{ngfw_st_template_name}',
                "orgReplacement":[{
                  "existingOrg":{
                    "organizationName":source_org
                    },
                "newOrg":{
                  "organizationName":target_org
                    }
                }]
              }})
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
    response = requests.post(f'{self.director_url}:{self.rest_api_port}/vnms/template/cloneTemplate', headers=headers, data=payload)
    if response.status_code == 200:
      logging.info(f"Service Template {ngfw_st_template_name} was cloned from {source_org} to {target_org} successfully.\n")
      return response
    else:
      response.raise_for_status()

  def delete_ngfw_service_template(self,ngfw_st_template_name=None):
    '''
    Method to delete a NGFW service template listed on Versa Director API

    :Inputs: target template name -> String
    :Outputs: Response from API call -> TBD
    '''    
    payload = json.dumps({"delete-template":{"name":f"{ngfw_st_template_name}"}})
    headers = {'Accept': 'application/vnd.yang.data+json', 'Content-Type': 'application/vnd.yang.data+json', 'Authorization': f'Bearer {self.access_token}'}
    response = requests.post(f'{self.director_url}:{self.rest_api_port}/api/config/nms/actions/_operations/delete-template', headers=headers, data=payload)
    if response.status_code == 200:
      logging.info(f"Service Template {ngfw_st_template_name} was deleted successfully")
      return response
    else:
      response.raise_for_status()

if __name__ == '__main__':
  '''
  This is the main entry point to this python script. This is just to list all the example API calls made using the DirectorAccess class.

  '''  
  '''
  This is the main entry point to this python script. This script downloads the templates associated with Versa SASE Gateways at a deep level and generates json and yaml
  file with the Name and Category provided by config.yml file in the current directory. Further it also downloads juniper style template config.

  :Inputs: config.yml -> File Object
  :Outpus: templated configuration in yaml,json and Juniper style formats -> Files

  ''' 
  ## start of standard header script ##
  config_file = 'config.yml'
  template_directory = 'vgw-templates'
  d = DirectorAccess(config_file)
  region,tenancy,access_token,refresh_token  = d.generate_token()
  tenancy = os.environ.get("V_TENANCY")
  region = os.environ.get("V_REGION")
  with open(config_file,'r') as fh:
    director_data = yaml.safe_load(fh)
  config_search_key = '_'.join([region,tenancy])
  this_director = director_data[config_search_key]
  template_dataset = this_director['vgw_templates']
  for this_template in template_dataset:
    template_type = this_template['Category']
    st_name = this_template['Name']
    cwd = os.getcwd()
    dirpath = os.path.join(cwd,template_directory,region,tenancy,f"{template_type} Templates")
    try: 
      os.makedirs(dirpath) 
    except OSError as error: 
      print(f"{dirpath} exists") 
    result_tmpl = d.get_service_template(st_name)

    # storing config in YAML format
    yamlfilepath = os.path.join(dirpath, f"{st_name}.yml")
    with open (yamlfilepath,"w") as fh:
      yaml.dump(result_tmpl,fh,indent=2)
    print(f"{st_name}.yml was created successfully")

    # storing config in JSON format
    jsonfilepath = os.path.join(dirpath, f"{st_name}.json")
    with open (jsonfilepath,"w") as fh:
      json.dump(result_tmpl,fh,indent=2)
    print(f"{st_name}.json was created successfully")

    if template_type == 'SDWAN Post Staging':
      continue
    # storing config in Juniper format
    jnprfilepath = os.path.join(dirpath, f"{st_name}.cfg")
    result_tmpl_juniper = d.get_service_template_juniper(st_name)
    with open (jnprfilepath,"w") as fh:
      fh.write(result_tmpl_juniper)
    print(f"{st_name}.cfg Juniper Style config was created successfully")
  





