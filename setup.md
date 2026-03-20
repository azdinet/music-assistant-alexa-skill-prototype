# Guide d'Installation Complet : Music Assistant ↔ Alexa Skill

Ce document récapitule l'intégralité de l'architecture et des étapes de configuration nécessaires pour faire fonctionner le lecteur expérimental Alexa avec Music Assistant, via une Skill Amazon Custom hébergée localement sur Home Assistant.

## 🏗️ Architecture Globale

Voici comment les différents éléments communiquent :

1. **Music Assistant** prépare un flux audio continu (mix, fondu, enchaînement) exposé sur le réseau local (`http://IP:8097`).
2. **Le Provider Alexa (dans MA)** notifie notre **Add-on HA (Skill)** d'une nouvelle URL à lire.
3. **L'Add-on HA** "nettoie" l'URL (force le `https://` et retire le port `8097`) pour satisfaire les exigences de sécurité d'Alexa.
4. **L'API de l'Add-on** est exposée sur internet via un pont **Nginx / DuckDNS**.
5. **Amazon Alexa** interroge ce pont via notre **Custom Skill**, récupère la bonne URL, et l'enceinte Echo lance la lecture.
6. Pour déclencher tout ça sans parler ("télécommande" depuis l'interface MA), MA lance secrètement une **Routine Alexa** via `Alexa Media Player` (HACS).

---

## 🛠️ 1. Configuration de l'Add-on Home Assistant

1. Ajoutez votre dépôt GitHub contenant ce code dans **Paramètres > Modules complémentaires > Boutique des modules**.
2. Installez le module **Music Assistant Alexa Skill**.
3. Dans l'onglet **Configuration** de l'Add-on :
   * Renseignez `MA_HOSTNAME`. (*Ex: l'URL publique de votre flux MA, qui servira de base si besoin*).
4. Assurez-vous que le port réseau local de l'API de la skill est bien exposé (ex: port **5000**).
5. **Démarrez** (ou Reconstruisez si mise à jour du code) le module complémentaire.
   * *Note système : le code a été modifié (fichiers `ma_routes.py` et `data.py`) pour convertir systématiquement à la volée le flux `http://...:8097` en `https://...` sans le port.*

---

## 🌐 2. Le Proxy Inverse (Nginx / DuckDNS)

Amazon exige un point de terminaison strict en HTTPS (port 443).
Il faut donc lier votre domaine (ex: `musiquedumuguet.duckdns.org`) à l'Add-on.

**Dans Nginx Proxy Manager :**
* **Domain Names :** `musiquedumuguet.duckdns.org`
* **Forward Hostname / IP :** L'adresse IP locale de Home Assistant (ex: `192.168.1.2`)
* **Forward Port :** `5000` (Le port de l'Add-on)
* **Scheme :** `http` (Car Nginx fait la traduction entre le HTTPS public et le HTTP local).

---

## 🗣️ 3. La Custom Skill (Developer Console Amazon)

Il faut créer la compétence au niveau d'Amazon.

1. Allez sur la [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).
2. Créez une nouvelle **Custom Skill** (Gérée par vous-même).
3. Dans **Interaction Model > Invocation** :
   * Définissez un **Skill Invocation Name** naturel. Exemple : `assistant musical`.
4. Sauvegardez et cliquez sur **Build Model**.
5. Dans la rubrique **Endpoint** :
   * Cochez **HTTPS**.
   * Dans la **Default Region**, mettez la racine stricte de votre proxy : **`https://musiquedumuguet.duckdns.org/`**
     *(Attention : N'ajoutez PAS `/alexa` à la fin. Le serveur Python attend les instructions vocales à la racine `/` !).*
   * Choisissez l'option du certificat SSL : *"My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"*.
6. Enregistrez les Endpoints.

---

## 🎵 4. Côté Music Assistant

1. Dans Music Assistant, allez dans **Settings > Providers**.
2. Assurez-vous d'ajouter (si ce n'est pas déjà fait) le fournisseur **Alexa Player**.
3. *Astuce optionnelle* : Si vous voulez de la radio, installez le fournisseur **Radio Browser** (gratuit, sans compte) ou **TuneIn** (nécessite de configurer votre compte avec des favoris enregistrés).

*(À ce stade, si vous demandez à l'oral "Alexa, ouvre assistant musical", la dernière musique envoyée par MA devrait jouer !).*

---

## 🪄 5. La Pièce Maîtresse : La Routine de "Télécommande"

C'est ce qui permet de cliquer sur "Play" dans l'application Music Assistant et que l'enceinte réagisse toute seule, sans commande vocale.
 Music Assistant utilise l'intégration **Alexa Media Player (HACS)** pour exécuter une routine en tâche de fond sur l'enceinte.

**Dans l'application mobile Amazon Alexa (sur votre téléphone) :**
1. Allez dans **Plus** > **Routines** > **+** (Créer une routine).
2. **Nom de la Routine :** Libellé facultatif, mais mettez `MA Play`.
3. **Quand cela se produit (When) :** 
   * Sélectionnez **Voix**.
   * Tapez exactement : **`MA Play`** *(C'est LE mot clé figé dans le code de Music Assistant).*
4. **Action :**
   * Descendez tout en bas et choisissez **Personnalisé (Custom)**.
   * Renseignez textuellement la commande pour lancer votre skill : **`ouvre assistant musical`**.
5. **Depuis (L'appareil) :** 
   * Sélectionnez : **L'appareil auquel vous parlez**.
6. **Sauvegardez !**

*(Il y a désormais un lien direct invisible : "Bouton Play UI" ➔ HACS `MA Play` ➔ Routine App ➔ "ouvre assistant musical" ➔ API Web.* 😎).

---

## 🔍 Dépannage rapide

* **Alexa répond qu'elle ne comprend pas :** Vérifiez que vous utilisez bien le Nom d'Invocation (*Invocation Name*) exact compilé dans la Developer Console.
* **L'Url reste figée sur `http://...8097` sur la page `/status` :** L'Add-on n'a pas pris le dernier code : faites un **Reconstruire (Rebuild)** depuis Home Assistant.
* **Le "Play" sur le navigateur MA ne fait rien sur l'enceinte :** La routine `MA Play` est mal configurée sur votre téléphone ou Alexa Media Player est déconnecté dans Home Assistant.
* **Je ne peux pas faire "Passer à la suivante" avec ma voix ("this is a radio") :** C'est normal. Music Assistant envoie un flux infini. Pour changer de titre, faites "Next" via l'interface Music Assistant, il modifiera le son à l'intérieur du flux sans que l'enceinte ne s'en rende compte !
