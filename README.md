# 🍑 **Culo** 🍑
#### Il bot di Discord più inutile del mondo *(o almeno lo era all'inizio dello sviluppo)*.
#### Nato come scherzo tra amici, è cresciuto e diventato un vero e proprio bot 
##
### Requisiti:
- [Python 3.9+](https://www.python.org/downloads/)
- Un [token](https://discord.com/developers/applications) per il bot
- [Discord.py Rewrite](https://discordpy.readthedocs.io/en/latest/)
- [youtube_dl](https://youtube-dl.org/)
- [ffmpeg](https://ffmpeg.org/download.html)
##
### **Features:**
- #### Prefisso del bot dinamico e modificabile server per server *(default:* 🍑 *)*
  - Basta scrivere `🍑prefisso <il prefisso>` per modificare il prefisso del bot nel server
  - Se te lo dimentichi scrivi `prefisso?`
- #### Comandi 🛠️
  - `chisono` rivela la tua vera identità 🙃
  - `scorreggia` fai rischiare le mutande al bot 😬
  - `pinga <@utente> <quantità>` sveglia il tuo amico a suoni di ping
  - `raduna <#canale>` riunisci tutti i tuoi amici nella stessa chat vocale **(solo per amministratori)**
  - `cancella <quantità>` cancella una certa quantità di messaggi **(solo per chi può cancellare messaggi)**
  - `temperatura` se il bot gira su un raspberry stampa la temperatura della CPU **(solo per il proprietario del bot)**
- #### Eventi 📆
  - il bot può rispondere a certi messaggi 😨 non sono molti ma piano piano aumentano
  - prova a scrivere `bravo bot` 😉
- #### Loops ⌚🔄
  - Ogni tot minuti il bot esegue qualche comando ⏰
- #### Musica 🎼🎵🎶
  - `connetti` per far entrare il bot nel canale vocale in cui ti trovi
  - `play <canzone>` per riprodurre una canzone
  - `pausa` per pausare la canzone in riproduzione
  - `riprendi` per riprendere la canzone pausata
  - `skip` per saltare la canzone corrente e passare alla prossima nella coda
  - `coda` stampa la lista di canzoni in coda
  - `in_riproduzione` stampa la canzone corrente
  - `volume <0-100>` imposta il volume del bot *(default: 50)*
  - `esci` stoppa la musica e fa uscire il bot **(cancella la coda)**
- ### Censura ❌🤫
  - `censura <@utente>` aggiunge/toglie un utente dalla lista di censura **(solo per amministratori)**
  - `lista_censura` stampa la lista di utenti censurati *(che non possono scrivere e parlare)* **(solo per amministratori)**
- ### Info 💁📂
  - `userinfo <@utente>` stampa alcune informazioni su un utente particolare
  - `serverinfo` stampa alcune informazioni sul server discord
  - `lista_server` stampa la lista di server in cui si trova il bot **(solo per il proprietario del bot)**
##
### To-Do List
#### Cose da aggiungere al bot:
- [x] Prefissi
- [x] Comandi
- [x] Eventi *(non risponde a molti messaggi ancora)*
- [x] Info
- [ ] Loops ***(non ha molti usi al momento)***
- [x] Musica
- [ ] Censura ***(ha bisogno di un rewrite)***
- [ ] Meteo
- [ ] Image processing
