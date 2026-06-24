"""
================================================================================
Option 1 : Tableau de bord « flux entropique »
Système CBU-X — Thermodynamique économique
Auteur : Marc Daghar
================================================================================
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Configuration globale
np.random.seed(42)
ANNEE_DEBUT = 2020
ANNEE_FIN = 2026
PRODUITS = ['Céréales', 'Phosphates', 'Textiles', 'Composants électroniques', 'Oléagineux']

# =============================================================================
# SECTION 1 : Génération des données synthétiques
# =============================================================================

def generer_donnees_commerce():
    """
    Génère des données synthétiques d'import/export Tunisie-France
    avec des tendances réalistes et bruit gaussien.

    Returns:
        pd.DataFrame: Données commerciales synthétiques
    """
    annees = list(range(ANNEE_DEBUT, ANNEE_FIN + 1))
    data = []

    for annee in annees:
        for produit in PRODUITS:
            # Tendances sectorielles différenciées
            if produit == 'Phosphates':
                base_export = 120 + 8 * (annee - ANNEE_DEBUT)
                base_import = 20 + 2 * (annee - ANNEE_DEBUT)
            elif produit == 'Céréales':
                if annee <= 2024:
                    base_export = 80 - 3 * (annee - ANNEE_DEBUT)
                else:
                    base_export = 80 - 3 * 4 - 10 * (annee - 2024)
                base_import = 30 + 5 * (annee - ANNEE_DEBUT)
            elif produit == 'Textiles':
                base_export = 60 - 2 * (annee - ANNEE_DEBUT)
                base_import = 40 + 3 * (annee - ANNEE_DEBUT)
            elif produit == 'Composants électroniques':
                base_export = 30 + 6 * (annee - ANNEE_DEBUT)
                base_import = 80 + 10 * (annee - ANNEE_DEBUT)
            else:  # Oléagineux
                base_export = 50 - 1 * (annee - ANNEE_DEBUT)
                base_import = 60 + 2 * (annee - ANNEE_DEBUT)

            # Bruit gaussien
            export = max(0, base_export + np.random.normal(0, 5))
            import_ = max(0, base_import + np.random.normal(0, 5))

            data.append({
                'annee': annee,
                'produit': produit,
                'export_tunisie_france_millions_usd': round(export, 2),
                'import_tunisie_france_millions_usd': round(import_, 2)
            })

    return pd.DataFrame(data)

# =============================================================================
# SECTION 2 : Calcul du flux entropique
# =============================================================================

def calculer_flux_entropique(df):
    """
    Calcule le flux entropique Φ(t) = Import - Export

    Args:
        df: DataFrame avec colonnes import/export

    Returns:
        pd.DataFrame: DataFrame enrichi avec flux entropique
    """
    df = df.copy()
    df['flux_entropique_millions_usd'] = (
        df['import_tunisie_france_millions_usd'] - 
        df['export_tunisie_france_millions_usd']
    )
    return df

# =============================================================================
# SECTION 3 : Indicateur de bifurcation Λ
# =============================================================================

def calculer_lambda(df, r=0.05, E_dot_low=1000):
    """
    Calcule le paramètre de bifurcation Λ(t) = D(t) * r / Ẽ_low

    Args:
        df: DataFrame avec flux entropique
        r: Taux d'intérêt implicite (défaut 5%)
        E_dot_low: Taux de production d'énergie utile (défaut 1000)

    Returns:
        dict: Valeurs de D(t), Λ(t), et statut de stabilité
    """
    flux_annuel = df.groupby('annee')['flux_entropique_millions_usd'].sum()
    dette_cumulative = flux_annuel.cumsum()
    lambda_values = (dette_cumulative * r) / E_dot_low

    # Seuil critique empirique
    lambda_c = 0.5

    return {
        'dette': dette_cumulative.to_dict(),
        'lambda': lambda_values.to_dict(),
        'lambda_c': lambda_c,
        'stable': {annee: (lam < lambda_c) for annee, lam in lambda_values.items()}
    }

# =============================================================================
# SECTION 4 : Visualisation
# =============================================================================

def generer_graphique(df, output_dir='.'):
    """
    Génère les graphiques des flux entropiques

    Args:
        df: DataFrame avec flux entropique
        output_dir: Répertoire de sortie
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Graphique 1 : Flux total par année
    flux_annuel = df.groupby('annee')['flux_entropique_millions_usd'].sum().reset_index()
    colors = ['#2ecc71' if x < 0 else '#e74c3c' for x in flux_annuel['flux_entropique_millions_usd']]

    ax1.bar(flux_annuel['annee'], flux_annuel['flux_entropique_millions_usd'], 
            color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax1.set_xlabel('Année', fontsize=12)
    ax1.set_ylabel('Flux entropique Φ(t) [millions USD]', fontsize=12)
    ax1.set_title('Flux entropique total Tunisie-France (Import - Export)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xticks(flux_annuel['annee'])

    # Graphique 2 : Par produit (dernière année)
    df_2026 = df[df['annee'] == ANNEE_FIN]
    produits = df_2026['produit']
    flux_produit = df_2026['flux_entropique_millions_usd']
    colors2 = ['#2ecc71' if x < 0 else '#e74c3c' for x in flux_produit]

    ax2.barh(produits, flux_produit, color=colors2, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('Flux entropique Φ(t) [millions USD]', fontsize=12)
    ax2.set_title(f'Flux entropique par produit ({ANNEE_FIN})', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--', axis='x')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/flux_entropique.png', dpi=300, bbox_inches='tight')
    plt.show()
    return fig

# =============================================================================
# SECTION 5 : Rapport Markdown
# =============================================================================

def generer_rapport(df, lambda_data, output_dir='.'):
    """
    Génère un rapport d'analyse complet en Markdown

    Args:
        df: DataFrame avec flux entropique
        lambda_data: Données du paramètre Λ
        output_dir: Répertoire de sortie
    """
    flux_total = df['flux_entropique_millions_usd'].sum()
    tendance = "détérioration" if flux_total > 0 else "amélioration"

    rapport = f"""# Analyse du flux entropique Tunisie-France ({ANNEE_DEBUT}-{ANNEE_FIN})

## Résumé exécutif
Le flux entropique total sur la période {ANNEE_DEBUT}-{ANNEE_FIN} s'élève à **{flux_total:.2f} millions USD**.
Cette valeur indique une **{tendance}** : la Tunisie est **{'importatrice nette' if flux_total > 0 else 'exportatrice nette'}** de valeur vis-à-vis de la France.

## Indicateur de bifurcation Λ(t)

| Année | Dette D(t) [M$] | Λ(t) | Statut |
|-------|-----------------|------|--------|
"""

    for annee in sorted(lambda_data['lambda'].keys()):
        dette = lambda_data['dette'][annee]
        lam = lambda_data['lambda'][annee]
        statut = "✅ Stable" if lambda_data['stable'][annee] else "⚠️ Critique"
        rapport += f"| {annee} | {dette:.2f} | {lam:.4f} | {statut} |\n"

    rapport += f"""
\n**Seuil critique** : Λ_c = {lambda_data['lambda_c']}

## Tendances par produit ({ANNEE_FIN})
"""

    df_2026 = df[df['annee'] == ANNEE_FIN]
    for _, row in df_2026.iterrows():
        statut = "déficitaire" if row['flux_entropique_millions_usd'] > 0 else "excédentaire"
        rapport += f"\n- **{row['produit']}** : {statut} de {abs(row['flux_entropique_millions_usd']):.2f} M$ USD."

    rapport += """

## Leviers de réduction proposés
1. **Transformation locale des phosphates** : Développer une industrie de transformation (engrais, acide phosphorique) pour capter la valeur ajoutée au lieu d'exporter le minerai brut.
2. **Circuits courts agricoles** : Réduire les importations céréalières via l'agriculture régénérative (permaculture) et la souveraineté alimentaire.
3. **Intégration monétaire régionale** : Utiliser le CBU-X (panier RUB+UAH+GEL+TRY) pour réduire les coûts de transaction et les fluctuations de change.

## Formulation mathématique

```
Φ(t) = Σ_p (M_{p,t} - X_{p,t})          [Flux entropique]
D(t) = ∫_0^t Φ(τ) dτ                      [Dette cumulative]
Λ(t) = D(t) · r / Ẽ_low                   [Paramètre de bifurcation]
```

---
*Généré par le système CBU-X — Sadaqa-BRI Framework*
"""

    with open(f'{output_dir}/README_option1.md', 'w', encoding='utf-8') as f:
        f.write(rapport)

    return rapport

# =============================================================================
# SECTION 6 : Point d'entrée principal
# =============================================================================

def main():
    """Exécution complète de l'Option 1"""
    print("=" * 60)
    print("🔄 OPTION 1 : FLUX ENTROPIQUE (Thermodynamique économique)")
    print("=" * 60)

    print("\n📊 Génération des données commerciales synthétiques...")
    df = generer_donnees_commerce()

    print("🔥 Calcul du flux entropique Φ(t)...")
    df = calculer_flux_entropique(df)

    print("📈 Calcul du paramètre de bifurcation Λ(t)...")
    lambda_data = calculer_lambda(df)

    print("💾 Sauvegarde du CSV...")
    df.to_csv('donnees_commerce_synthetiques.csv', index=False)

    print("📉 Génération des graphiques...")
    generer_graphique(df)

    print("📝 Génération du rapport...")
    generer_rapport(df, lambda_data)

    print("\n" + "=" * 60)
    print("✅ OPTION 1 TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)
    print("📁 Fichiers générés :")
    print("   • donnees_commerce_synthetiques.csv")
    print("   • flux_entropique.png")
    print("   • README_option1.md")

if __name__ == "__main__":
    main()
