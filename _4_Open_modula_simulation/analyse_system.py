#!/usr/bin/env python3

"""
Guide de configuration du traitement parallèle pour simulations TEASER
Explications détaillées et configurations recommandées
"""

import multiprocessing as mp
import psutil
import time
from pathlib import Path

def analyze_system_capabilities():
    """Analyse les capacités de votre système"""
    print("=" * 60)
    print("ANALYSE DE VOTRE SYSTÈME")
    print("=" * 60)
    
    # CPU
    cpu_count = mp.cpu_count()
    cpu_freq = psutil.cpu_freq()
    print(f"💻 Processeur:")
    print(f"   - Nombre de cœurs: {cpu_count}")
    if cpu_freq:
        print(f"   - Fréquence: {cpu_freq.current:.0f} MHz")
    
    # RAM
    memory = psutil.virtual_memory()
    print(f"🧠 Mémoire:")
    print(f"   - RAM totale: {memory.total / 1e9:.1f} GB")
    print(f"   - RAM disponible: {memory.available / 1e9:.1f} GB")
    print(f"   - RAM utilisée: {memory.percent:.1f}%")
    
    # Disque
    disk = psutil.disk_usage('/')
    print(f"💾 Disque:")
    print(f"   - Espace total: {disk.total / 1e9:.1f} GB")
    print(f"   - Espace libre: {disk.free / 1e9:.1f} GB")

def recommend_worker_configuration(cpu_count: int, ram_gb: float, simulation_count: int):
    """Recommande la configuration optimale de workers"""
    print("\n" + "=" * 60)
    print("RECOMMANDATIONS DE CONFIGURATION")
    print("=" * 60)
    
    # Estimation mémoire par worker (OpenModelica + modèle)
    memory_per_worker_gb = 2.0  # Estimation conservatrice
    
    # Workers basés sur CPU (laisser 1 cœur pour l'OS)
    cpu_based_workers = max(1, cpu_count - 1)
    
    # Workers basés sur RAM (garder 2GB pour l'OS)
    ram_based_workers = max(1, int((ram_gb - 2) / memory_per_worker_gb))
    
    # Workers basés sur la charge de travail
    if simulation_count < 10:
        workload_workers = min(simulation_count, 2)
    elif simulation_count < 100:
        workload_workers = min(simulation_count, 4)
    else:
        workload_workers = 8  # Max recommandé pour stabilité
    
    # Recommandation finale (le minimum des contraintes)
    recommended_workers = min(cpu_based_workers, ram_based_workers, workload_workers)
    
    print(f"📊 Analyse des contraintes:")
    print(f"   - Contrainte CPU: {cpu_based_workers} workers (CPUs: {cpu_count})")
    print(f"   - Contrainte RAM: {ram_based_workers} workers (RAM: {ram_gb:.1f}GB)")
    print(f"   - Contrainte charge: {workload_workers} workers ({simulation_count} simulations)")
    
    print(f"\n🎯 RECOMMANDATION FINALE: {recommended_workers} workers")
    
    # Estimation des performances
    estimated_time_sequential = simulation_count * 95  # 95s par simulation
    estimated_time_parallel = estimated_time_sequential / recommended_workers
    
    print(f"\n⏱️  Estimation des temps:")
    print(f"   - Séquentiel: {estimated_time_sequential/3600:.1f} heures")
    print(f"   - Parallèle ({recommended_workers} workers): {estimated_time_parallel/3600:.1f} heures")
    print(f"   - Accélération: {recommended_workers:.1f}x")
    
    return recommended_workers

def create_test_configurations():
    """Crée différentes configurations de test"""
    print("\n" + "=" * 60)
    print("CONFIGURATIONS DE TEST SUGGÉRÉES")
    print("=" * 60)
    
    configs = [
        {
            "name": "Test basique",
            "workers": 1,
            "simulations": 5,
            "description": "Test de fonctionnement de base"
        },
        {
            "name": "Test parallélisme",
            "workers": 2,
            "simulations": 10,
            "description": "Vérifier que le parallélisme fonctionne"
        },
        {
            "name": "Test performance",
            "workers": 4,
            "simulations": 50,
            "description": "Mesurer l'accélération réelle"
        },
        {
            "name": "Production",
            "workers": "auto",
            "simulations": "all",
            "description": "Configuration finale pour toutes les simulations"
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. {config['name']}:")
        print(f"   - Workers: {config['workers']}")
        print(f"   - Simulations: {config['simulations']}")
        print(f"   - But: {config['description']}")

def generate_configuration_code(workers: int, max_simulations: int = None):
    """Génère le code de configuration"""
    print("\n" + "=" * 60)
    print("CODE DE CONFIGURATION")
    print("=" * 60)
    
    print(f"""
# Configuration recommandée pour votre système
def main():
    PACKAGE_PATH = r"C:/Users/hp/TEASEROutput/Project/package.mo"
    AIXLIB_PATH = r"C:/AixLib-main/AixLib-main/AixLib/package.mo"
    OUTPUT_DIR = r"_4_Open_modula_simulation/simulation_results_optimized"
    
    # ÉTAPE 1: TEST BASIQUE (recommandé avant production)
    print("🧪 Test avec {workers} workers et {max_simulations or 'toutes les'} simulations...")
    
    results = run_optimized_simulations(
        PACKAGE_PATH, 
        AIXLIB_PATH, 
        OUTPUT_DIR,
        max_simulations={max_simulations or 'None'},  # None = toutes les simulations
        max_workers={workers}        # Nombre de workers recommandé
    )
    
    # ÉTAPE 2: Si le test fonctionne bien, augmentez progressivement
    # max_workers=2 → 4 → 6 → 8 selon vos résultats
""")

def monitor_system_during_simulation():
    """Guide pour surveiller le système pendant les simulations"""
    print("\n" + "=" * 60)
    print("SURVEILLANCE DU SYSTÈME")
    print("=" * 60)
    
    print("""
🔍 Pendant les simulations, surveillez:

1. UTILISATION CPU:
   - Ouvrez le Gestionnaire des tâches (Ctrl+Shift+Esc)
   - Onglet "Performance" → CPU
   - L'utilisation devrait être élevée mais pas 100% constant

2. UTILISATION MÉMOIRE:
   - Même onglet → Mémoire
   - Si >90%, réduisez le nombre de workers

3. UTILISATION DISQUE:
   - Même onglet → Disque
   - Activité élevée normale pendant les simulations

4. PROCESSUS OPENMODELICA:
   - Onglet "Processus"
   - Cherchez "omc" ou "OpenModelica"
   - Vous devriez voir plusieurs processus actifs

⚠️  SIGNAUX D'ALARME:
   - RAM >95% : ARRÊTEZ et réduisez les workers
   - CPU 100% pendant >10 min : Possible blocage
   - Pas d'activité disque : Possible problème
   - Messages d'erreur répétés : Vérifiez les logs
""")

def troubleshooting_guide():
    """Guide de résolution des problèmes"""
    print("\n" + "=" * 60)
    print("RÉSOLUTION DE PROBLÈMES")
    print("=" * 60)
    
    problems = [
        {
            "problem": "Les simulations ne démarrent pas",
            "solutions": [
                "Vérifiez les chemins PACKAGE_PATH et AIXLIB_PATH",
                "Testez d'abord avec 1 worker",
                "Vérifiez les logs dans simulation_log.txt"
            ]
        },
        {
            "problem": "Erreurs 'Out of Memory'",
            "solutions": [
                "Réduisez le nombre de workers",
                "Fermez les autres applications",
                "Augmentez la mémoire virtuelle Windows"
            ]
        },
        {
            "problem": "Simulations très lentes",
            "solutions": [
                "Vérifiez l'utilisation CPU/RAM",
                "Réduisez le nombre de workers si surcharge",
                "Utilisez un SSD si possible"
            ]
        },
        {
            "problem": "Blocages fréquents",
            "solutions": [
                "Réduisez à 2 workers maximum",
                "Augmentez la tolérance (1e-3)",
                "Vérifiez la stabilité avec 1 worker d'abord"
            ]
        }
    ]
    
    for i, item in enumerate(problems, 1):
        print(f"\n{i}. PROBLÈME: {item['problem']}")
        print("   SOLUTIONS:")
        for solution in item['solutions']:
            print(f"   - {solution}")

def main():
    """Fonction principale d'analyse et recommandations"""
    
    print("🔧 CONFIGURATION OPTIMALE POUR VOS SIMULATIONS TEASER")
    print("=" * 80)
    
    # Analyser le système
    analyze_system_capabilities()
    
    # Obtenir les informations système
    cpu_count = mp.cpu_count()
    memory_gb = psutil.virtual_memory().total / 1e9
    simulation_count = 1000  # Vos 1000 bâtiments
    
    # Recommandations
    recommended_workers = recommend_worker_configuration(cpu_count, memory_gb, simulation_count)
    
    # Configurations de test
    create_test_configurations()
    
    # Code de configuration
    generate_configuration_code(recommended_workers, 10)  # Test avec 10 simulations
    
    # Surveillance
    monitor_system_during_simulation()
    
    # Résolution de problèmes
    troubleshooting_guide()
    
    print("\n" + "=" * 80)
    print("🎯 PLAN D'ACTION RECOMMANDÉ:")
    print("=" * 80)
    print(f"""
1. COMMENCEZ PAR UN TEST:
   - 1 worker, 5 simulations
   - Vérifiez que tout fonctionne

2. TESTEZ LE PARALLÉLISME:
   - 2 workers, 10 simulations
   - Mesurez l'accélération

3. OPTIMISEZ PROGRESSIVEMENT:
   - Augmentez jusqu'à {recommended_workers} workers
   - Testez avec 50-100 simulations

4. PRODUCTION:
   - Configuration finale validée
   - Lancez vos 1000 simulations

5. SURVEILLEZ:
   - Gestionnaire des tâches ouvert
   - Logs de simulation
   - Arrêtez si problèmes
""")

if __name__ == "__main__":
    main()