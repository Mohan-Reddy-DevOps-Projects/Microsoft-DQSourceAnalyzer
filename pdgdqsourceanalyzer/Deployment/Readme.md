## One time Manual Steps for deployment:

### ACR Creation - One Time Activity

- Create an ACR called dataqualityacr in fixed assets resource group. Reason - To try EV2 scripts on local, we need to push docker images to a container registry. Although it's not required in actual pipeline as there we use a common registry. (See file 'image_metadata/dataquality.json')

## Generate T4 Template Files
- Go to project top directory
- Run 'bash generateT4TemplateFiles.sh'

## How to Run EV2 scripts locally
- Use special EV2 powershell to run commands 
    <a>https://ev2docs.azure.net/references/cmdlets/Intro.html</a>

- Open powershell and navigate to Deployment folder (DataQuality/src/Deployment)

- To setup Infra: ./Scripts/DataQualityDeployInfra.ps1
    - NOTE: Use 'Test' rollout type when asked in CLI.

- To setup AKS: ./Scripts/DataQualityDeployAKS.ps1    

- To setup Secrets: ./Scripts/DataQualityDeploySecrets.ps1    

- Complile C# Code: ../../build/compileDotnetService.sh src/Services/DataQuality/Source Release

- Run ./buildDocker.sh to push docker image to our personal ACR instead of cdpxlinux shared one.

- To deploy service: ./DataQualityDeployService.ps1
    
