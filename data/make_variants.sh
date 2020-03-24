SIM=1.0,0.9
MOD=0.9,0.7
DIS=0.7,0.0

./prepare.py render -i gold_picked/data -s style.json -o simsim -r mrmechko/trips-annotate --use-reparsed true -g $SIM -c $SIM 
./prepare.py render -i gold_picked/data -s style.json -o simmod -r mrmechko/trips-annotate --use-reparsed true -g $SIM -c $MOD
./prepare.py render -i gold_picked/data -s style.json -o simdis -r mrmechko/trips-annotate --use-reparsed true -g $SIM -c $DIS
./prepare.py render -i gold_picked/data -s style.json -o modmod -r mrmechko/trips-annotate --use-reparsed true -g $MOD -c $MOD
./prepare.py render -i gold_picked/data -s style.json -o simdis -r mrmechko/trips-annotate --use-reparsed true -g $SIM -c $DIS
./prepare.py render -i gold_picked/data -s style.json -o moddis -r mrmechko/trips-annotate --use-reparsed true -g $MOD -c $DIS
