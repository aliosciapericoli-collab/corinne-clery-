# Prompt Lovable — corinneclery.it

## Parte A — Prompt iniziale (GIÀ INVIATO il 18/08/2026, con `corinne-clery.json` allegato)

> Costruisci il sito istituzionale ufficiale di Corinne Cléry — attrice francese icona del cinema europeo (Histoire d'O, Bond Girl in Moonraker con Roger Moore, commedia italiana), oggi residente in un casale nella Tuscia — con la pagina del suo format video "Parlane con Corinne Cléry".
>
> IMPORTANTE — LEGGI PRIMA IL FILE ALLEGATO. In allegato trovi `corinne-clery.json`: contiene TUTTI i contenuti reali e verificati (anagrafica, biografia per epoche, timeline, filmografia cinema/TV/teatro/reality, aneddoti "Storie", sezione Tuscia e animali, press kit, SEO, fonti). Salvalo in `src/content/corinne-clery.json`, crea i tipi TypeScript corrispondenti in `src/content/types.ts` e alimenta OGNI pagina da lì. NON riscrivere i contenuti a memoria e NON inventare fatti, date, titoli di film, premi, dichiarazioni, recapiti o numeri di telefono: se un dato non è nel JSON, ometti il dato invece di inventarlo. Dove il JSON dice "DA COMPLETARE" mostra un segnaposto discreto, non un dato inventato. Rispetta anche le note `nota_validazione` e `nota_redazionale`: quei contenuti non vanno enfatizzati finché non validati.
>
> **Contesto** — Corinne Cléry è una delle poche vere icone internazionali del cinema che vivono in Italia: protagonista di Histoire d'O (1975), Bond Girl in Moonraker (1979), poi volto amatissimo di commedia italiana, TV e teatro, fino ai reality e al Premio Troisi 2026. Dal 2020 vive in un casale alle porte di Tuscania (Tuscia, provincia di Viterbo): il claim del sito è la sua frase «La Tuscia è casa mia». Il differenziale del progetto è il format video proprietario "Parlane con Corinne Cléry", girato nel casale.
>
> **Tono di voce** — Elegante, caldo, in prima persona dove possibile. Mai nostalgico-museale, mai gossip, mai sensazionalistico. I temi sensibili non compaiono. Frasi brevi, understatement francese, ironia leggera. Pubblico doppio: stampa/booking e pubblico affezionato + fandom Bond internazionale.
>
> **Direzione visiva** — Cinematografica ma contemporanea, "pellicola e campagna": avorio caldo #F4EDE1, nero pellicola #17130E, oro caldo #B8934A (accenti), bordeaux profondo #6E1E2B (CTA e format), verde oliva #66714F (Tuscia e animali). Token in index.css e tailwind.config, tema chiaro e scuro (lo scuro come una sala cinematografica). Tipografia: Fraunces o Cormorant Garamond per i titoli, Inter per il testo. Solo segnaposto eleganti al posto delle foto (nessun diritto ancora acquisito): gradienti di palette, monogramma "CC", alt text in italiano già scritti. Niente stock con volti, niente hotlink. Accessibilità AA.
>
> **Struttura prima build** — Home (hero, claim, 4 dati chiave, 3 focus card carriera, teaser format, 3 Storie, blocco Tuscia, footer) · Chi è Corinne (biografia a epoche + timeline interattiva) · La Carriera (Cinema / TV e teatro / Riconoscimenti + curiosità) · Storie (card + dettaglio per slug con fonte) · Parlane con Corinne Cléry (format, "in preparazione", come partecipare) · La Tuscia e gli animali · Press Kit · Contatti/Booking (modulo senza recapiti inventati).
>
> **Tecnica** — Mobile-first. SEO in italiano (query dominante "Corinne Clery" senza accento), Open Graph, sitemap, canonical, JSON-LD Person in home. Contenuti centralizzati nel JSON per predisporre una futura versione EN; questa build è solo in italiano.

---

## Parte B — Follow-up suggeriti (UNO ALLA VOLTA, con verifica in mezzo)

**B1 — Verifica fedeltà contenuti.** «Controlla pagina per pagina che ogni testo, data e titolo provenga da `src/content/corinne-clery.json`. Elenca eventuali contenuti che hai scritto tu e non provengono dal JSON, e sostituiscili o rimuovili.»

**B2 — Home: rifinitura hero e ritmo.** Da valutare dopo aver visto la preview: gerarchia del claim, contrasto dell'overlay, ordine delle sezioni.

**B3 — Timeline.** «Rendi la timeline navigabile per decenni (1950–1970–1980–1990–2000–2010–2020) con scroll orizzontale su mobile.»

**B4 — Pagina format.** Potenziare "Parlane con Corinne Cléry": griglia puntate segnaposto ("Prossimamente"), blocco proposte temi collegato al modulo contatti con tipo richiesta pre-selezionato.

**B5 — Press kit.** Bottone "Copia la bio", versione bio breve/media, nota diritti foto ben visibile.

**B6 — SEO check.** «Verifica meta title/description di ogni pagina: la keyword primaria è "Corinne Clery" senza accento, ma il nome nel testo visibile resta "Corinne Cléry" con l'accento. Controlla sitemap, canonical e JSON-LD Person.»

**B7 — Versione EN** (fase successiva, solo quando i contenuti IT sono validati da Corinne).

---

## Promemoria

- Ogni messaggio a Lovable consuma crediti: chiedere prima di inviare.
- `set_project_knowledge` sostituisce tutto: leggere prima con `get_project_knowledge`.
- Le foto reali arriveranno da: archivio personale di Corinne, shooting nel casale, Wikimedia
  Commons (licenze verificate), eventuali licenze editoriali per 2-3 immagini iconiche, frame del
  format.
