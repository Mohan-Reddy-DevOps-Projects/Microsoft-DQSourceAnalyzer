<#
.SYNOPSIS
Sets up all the required AKS resources for an Ev2 rollout.
#>

function InitializeRollout
{
    $RootPath = Split-Path $PSScriptRoot -Parent
    $rollout = New-AzureServiceRollout  -ServiceGroupRoot $RootPath -RolloutSpec RolloutSpecs\generated\RolloutSpec.AKS.Purview.DQS.DEV.wus2.json -EnableStrictValidation
    $rolloutId = $rollout.RolloutId
}

try {
    InitializeRollout 
}
catch {
    Write-Host "Error encountered in Data Quality AKS Rollout."
    throw
}
