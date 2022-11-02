# versa-director-api
## Introduction

  Versa Networks are one of the leading providers in the Software Defined WAN and Secure Access Services Edge as a Service. They have a defined set of network orchestration constructs that offer a single pane of glass to manage the entire fleet of Customer Edge and Provider Edge FlexVNF instances. The network configuration is heavily templatized and parameterized such that configuration compliance is a day 0 promise and not an after thought. As these template files are serialised in to JSON and Juniper Style configuration formats, the configuration tracking becomes easy with any version control system such as GitHub. 
  
  This repository maintains a minimal python software development kit, that abstract the authentication and configuraton template management methods, to make it easy for a Versa Networks user with the right level of access to get started with automating some of the business as usual tasks.
  
  Versa Networks have launched a promising newer automation and orchestration platform Versa Concerto, which will eventually remove the dependancies on regional Versa Director. Please contact Versa Networks to know more.
  
Reference: https://versa-networks.com/documents/datasheets/versa-concerto.pdf
  
  
## Idea

  Versa Networks SDWAN and SASE components are being orchestrated by their Versa Director Portals in three regions APAC, EMEA and US. The configuration base on the director portals are being exposed via their regional API gateways. These API gateways are secured by:
  - Access Control Lists for source IPv4 addresses of the API clients
  - Service accounts on the Versa Director Portals
  - OAuth
  
  Anyone who needs access the Versa Director Portal should contact their support channels to get an API client setup on these directors with set token limits and Access Control List updated with source IPv4 addresses of the API clients. Additionally, they can help RBAC roles and Organisational service accounts that need to be setup on the regional Versa Directors.
  
  With the API client ID, API Client Secret, Versa Director Service Account username and password, this repository can instantiate the objects to get the user started with automating. The authentication material will be securely encrypted with Native Python Cryptography library methods and stored in the temp directory of the respective operating systems. Users are recommended to explore better encryption systems such as Windows DPAPI, Public Cloud secret stores to suit their security compliance needs. 
  
  ## List of Methods
  1. generate_token - generation OAuth tokens, encrypt, store for reuse. Note the access tokens are limited and the user is supposed to generate access tokens periodically with the Refresh Token provided on the first basic authentication API calls. This method abstract all these complexities.
  2. run_get_api_call - wrapper method for any custom API GET call. The user may consult API documentation or explore the developer tools on the web browser, when accessing Versa Director for their use cases.
  3. get_orgs - gets the tenant organisation details.
  4. get_device_group - get details about a given device group.
  5. get_device_config - get the entire configuration of an SDWAN device in JSON format. Please note this method does not apply for SASE gateways.
  6. get_list_of_device_templates - get the list of device templates in an org.
  7. get_device_template - ask for a device template in JSON format.
  8. get_device_template_juniper - ask for a service template in Juniper style config format. This is the recommended format for configuration tracking as it makes it easier to compare the configuration constructs with that on the Versa Director GUI. The configuration snapshots are stored in this format and also Versa Support are very conversant with this format, which helps in troubleshooting.
  9. create_blank_ngfw_service_template - POST a blank NGFW service template.
  10. get_list_of_org_service_templates - get the list of service templates in an org.
  11. get_service_template - same as 7.
  12. clone_service_template - clone an existing service template.
  13. delete_ngfw_service_template - delete an existing service template.
