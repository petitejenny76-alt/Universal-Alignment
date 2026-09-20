# Security policy

Universal Alignment est un prototype expérimental de décision d’autorisation. Il ne doit pas être présenté comme une frontière de sécurité autonome.

Pour signaler un problème avant publication publique, utiliser un canal privé du propriétaire du dépôt. Ne joindre ni secrets, ni données personnelles, ni contenus de tiers non nécessaires à la reproduction.

Les rapports utiles doivent préciser : version/empreinte du pack, scénario minimal, décision attendue, décision observée et impact.

Les problèmes liés à l’exécution réelle (sandbox OS, TOCTOU, révocation, anti-rejeu, isolation des clés) sont importants même lorsqu’ils dépassent le code de décision fourni ici.

RC4 considère les noms de source comme insuffisants pour établir l’indépendance. Les producteurs d’évidence doivent être associés à des domaines de confiance provisionnés par l’hôte et utiliser des clés distinctes. Ce mécanisme empêche certains alias évidents, mais ne prouve pas que des processus, opérateurs ou capteurs sont réellement indépendants.