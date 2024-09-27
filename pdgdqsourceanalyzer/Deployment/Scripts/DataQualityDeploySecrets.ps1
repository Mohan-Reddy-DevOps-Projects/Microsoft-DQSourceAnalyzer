<#
.SYNOPSIS
Sets up all the required Secrets resources for an Ev2 rollout.
#>


function InitializeRollout
{
    $RootPath = Split-Path $PSScriptRoot -Parent
    $rollout = New-AzureServiceRollout  -ServiceGroupRoot $RootPath -RolloutSpec RolloutSpecs\generated\RolloutSpec.Secrets.Purview.DQS.DEV.wus2.json -EnableStrictValidation
    $rolloutId = $rollout.RolloutId
}

try {
    InitializeRollout 
}
catch {
    Write-Host "Error encountered in Data Quality Secrets Rollout."
    throw
}
