# Application Web — Registre des évidences RGPD

Cette application permet de centraliser les preuves qu'une entreprise met en place pour démontrer sa conformité au RGPD.

## Fonctionnalités

- Tableau de bord de suivi conformité
- Ajout d'une évidence RGPD
- Classement par catégorie
- Statut de conformité
- Téléversement de documents justificatifs
- Recherche et filtrage
- Export CSV
- Suppression d'une évidence

## Installation

```bash
cd rgpd_evidence_app
python -m venv venv
```

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Linux / macOS

```bash
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Accès

Ouvrir le navigateur :

```text
http://127.0.0.1:5000
```

## Exemple d'évidences RGPD

- Registre des activités de traitement
- Politique de confidentialité
- Preuve de consentement
- Contrat de sous-traitance
- Analyse d'impact DPIA/AIPD
- Procédure de notification CNIL
- Journal des demandes d'accès / rectification / suppression
- Politique de conservation des données
- Rapport d'audit sécurité
- Preuve de formation des collaborateurs

## Attention

Cette version est pédagogique. Pour une utilisation professionnelle, il faut ajouter :
- authentification utilisateurs ;
- rôles administrateur / auditeur / contributeur ;
- chiffrement des fichiers ;
- journalisation des actions ;
- sauvegardes ;
- hébergement HTTPS ;
- gestion des habilitations.
