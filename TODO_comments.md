# CTFd feedback export

- **Instance:** http://localhost:9042/ctfd/default
- **Exported:** 2026-05-26 19:49 UTC
- **Authenticated as:** admin
- **Challenges:** 34

## Challenge ratings & reviews

Participant upvotes/downvotes and optional review text (admin-only in CTFd).

### Shell 101 — pwd

Challenge id: 6 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Ajouter dans la description une commande forçant l'utilsateur à retourner dans son home | 2026-05-26T18:00:33.578425+00:00 |

### Shell 101 — cd

Challenge id: 7 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Modifier la description de ce challenge pour le changer en QCM | 2026-05-26T18:01:35.291118+00:00 |

### Shell 101 — mkdir

Challenge id: 8 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Changer le flag. Dans la description demander à l'utilisateur de donner le chemin absolu de 101 -> /home/user42/101 (Donner en indice cd + pwd) | 2026-05-26T18:04:24.480643+00:00 |

### Shell 101 — cp

Challenge id: 9 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Changer le flag.  Créer un script sur l'image de la VM check_shell101_cp qui compare l'output de `tree /home/user42/101` avec  ``` /home/user42/101/ ├── code │   ├── infinite_loop_timer.py │   └── read_dev_zero_until_eof.c ├── links │   ├── qrcode1 │   └── qrcode2 ├── memo1.txt ├── memo2.txt ├── memos └── works     ├── essay1.txt     └── essay2.txt  4 directories, 8 files ``` Et donne le flag shell1{$(tree /home/user42/101/ \| md5sum - \| awk '{print $1}')} -> shell1{2565827afcf8a63b73225e43883a54b2} | 2026-05-26T18:18:18.112525+00:00 |

### Shell 101 — mv

Challenge id: 10 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Même commentaire que pour "Shell 101 - cp" Script check_shell101_mv compare tree /home/user42/101 avec /home/user42/101/ ├── code │   ├── infinite_loop_timer.py │   └── read_dev_zero_until_eof.c ├── links │   ├── ubuntu │   └── wikipedia_linux ├── memos │   ├── memo1.txt │   └── memo2.txt ├── secret1.txt ├── secret2.txt └── works     ├── essay1.txt     └── essay2.txt  4 directories, 10 files  Et donne le flag shell1{d75ecdbb8076ef9eee610e0bc71e1cd2}  (résultat de tree /home/user42/101/ \| md5sum - \| awk '{print $1}') | 2026-05-26T18:26:08.751737+00:00 |

### Shell 101 — cat

Challenge id: 11 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Traduire le fichier .secret1.txt en français directement dans le rootfs de la VM. Les participants ne sont pas forcement à l'aise avec l'anglais. Utiliser les charactère de bordure UTF-8 pour encadrer les commandes (à la place des bloc de code markdown) ->plus lisible pour débutants | 2026-05-26T18:35:02.554495+00:00 |

### Shell 101 — micro

Challenge id: 12 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Traduire le fichier en francais. Supprimer les lignes vides pour éviter toute confusion. Replacer le flag. Faire un script check_shell101_micro qui vérifie avec grep si le fichier est correctement modifié. Le script doit donner des indications claires des tests qui ne fonctionne pas: ligne manquante à la fin du fichier, ligne en double toujours présente. ([ $(tail -n1 memo2.txt \| grep -c 'Convaincre un chat que je suis le chef') -eq 1 ] && [ $(grep -c 'Write a 3-sentence fanfiction between a brick and a toaster' memo2.txt) -eq 1 ] && echo "ok" \| \| echo ko) Le script donne le flag suivant: shell1{b51eeea2920ad9f39864d129cfcacc42} | 2026-05-26T18:49:17.249246+00:00 |

### Shell 101 — rm et rmdir

Challenge id: 13 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Remplacer le flag. Faire un script de validation shell101_rm qui vérifie [ "$(find /home/user42/101/ \| grep -c /home/user42/101/code)" -eq 0 ] && echo "Pas de dossi er 'code' OK" && [ "$(md5sum /home/user42/101/works/*)" = "70d8bf6b18efd7949d10f5d61485264b  /home/user42/10 1/works/essay2.txt" ] && echo OK  Le script explique clairement ce qui n'est pas correct  Lorsque tout est correct, le script donne le flag: shell1{d5a8519c77610b404dc97de591f56205} | 2026-05-26T19:40:05.332092+00:00 |

### Shell 101 — Archivage (tar)

Challenge id: 14 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Flag de lecture pour ce challenge: le donner clairement dans la description. Reduire le  nombre de point à 1 pour les challenges de lecture | 2026-05-26T19:43:38.461127+00:00 |

### Shell 101 — Livrable 1

Challenge id: 15 · summary: +0 / −1 (1 rating(s))

| User | Vote | Review | Date |
| --- | --- | --- | --- |
| kc123 | -1 | Changer le flag. Creer un script de validation dans le rootfs de la VM. Le script de validation fait un md5sum /mnt/host/.delivery_101.tar et compare avec le md5 attendu. Le flag est shell1{<le md5 de l'output de la commande ( md5sum /mnt/host/.delivery_101.tar )>} | 2026-05-26T19:48:47.665103+00:00 |

## Admin comments

Organizer discussion (CTFd `/api/v1/comments`, admin-only).

*(none)*
