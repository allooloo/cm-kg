cd /c/ALLOOLOO/AZURE
export PYTHONIOENCODING=utf-8
for p in "ca canadacentral" "uk uksouth" "fr francecentral" "nl westeurope" "de germanywestcentral" "au australiaeast" "sg southeastasia" "jp japaneast" "kr koreacentral" "us eastus"; do
  python provision_region.py $p stage >> stage-all.log 2>&1
done
echo "== STAGE ALL DONE $(date +%H:%M)" >> stage-all.log
sleep 1800
for p in "ca canadacentral" "uk uksouth" "fr francecentral" "nl westeurope" "de germanywestcentral" "au australiaeast" "sg southeastasia" "jp japaneast" "kr koreacentral" "us eastus"; do python provision_region.py $p check >> check-30.log 2>&1; done
echo "== CHECK +30 DONE $(date +%H:%M)" >> check-30.log
sleep 1800
for p in "ca canadacentral" "uk uksouth" "fr francecentral" "nl westeurope" "de germanywestcentral" "au australiaeast" "sg southeastasia" "jp japaneast" "kr koreacentral" "us eastus"; do python provision_region.py $p check >> check-60.log 2>&1; done
echo "== CHECK +60 DONE $(date +%H:%M)" >> check-60.log
