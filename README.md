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
  
  With the API client ID, API Client Secret, Versa Director Service Account username and password, this repository can instantiate the objects to get the user started with automating.
