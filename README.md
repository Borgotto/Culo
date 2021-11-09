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
- [BeautifulSoup 4.9+](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup)
- [lxml](https://lxml.de/installation.html)
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
  - `cancella <quantità> <modalità>` cancella una certa quantità di messaggi **(solo per chi può cancellare messaggi)**
  - `temperatura` se il bot gira su un raspberry stampa la temperatura della CPU **(solo per il proprietario del bot)**
- #### Urban Dictionary 📚
  - `wotd` ti fa sapere qual è la parola del giorno 📜
  - `parola_random` ti da la definizione di una parola totalmente a caso 🤣
  - `definisci <parola>` ti da la definizione della parola/frase passata
  - `set_wotd_channel <canale>` imposta il canale dove la pdg verrà inviata automaticamente **(solo per amministratori)**
  - `remove_wotd_channel` rimuove il canale dalla pdg automatica **(solo per amministratori)**
  - `restart_wotd_loop` riavvia il ciclo della parola del giorno **(solo per il proprietario del bot)**
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
- ### Info 💁📂
  - `userinfo <@utente>` stampa alcune informazioni su un utente particolare
  - `serverinfo` stampa alcune informazioni sul server discord
  - `lista_server` stampa la lista di server in cui si trova il bot **(solo per il proprietario del bot)**
- #### Eventi 📆
  - il bot può rispondere a certi messaggi 😨 non sono molti ma piano piano aumentano
  - prova a scrivere `bravo bot` 😉
- #### Loops ⌚🔄
  - Ogni tot minuti il bot esegue qualche comando ⏰
##
### To-Do List
#### Cose da aggiungere al bot:
- [x] Prefissi
- [x] Comandi
- [x] Eventi *(non risponde a molti messaggi ancora)*
- [x] Info
- [x] Loops ***(non ha molti usi al momento)***
- [x] Musica
- [x] Urban Dictionary: Word of the Day
- [x] Ubran Dictionary: Word definition
- [ ] Meteo
- [ ] Image processing
