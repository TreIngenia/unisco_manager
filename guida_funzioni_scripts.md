**Guida all'Uso delle Funzioni nel file **``

---

### 1. API Globale

``\
Effettua una chiamata `fetch` con configurazione standard per le API. Gestisce sessioni scadute e messaggi di errore.

**Esempio:**

```javascript
const result = await apiCall('/admin/api/users', { method: 'GET' });
```

``\
Mostra un alert e reindirizza al login in caso di sessione scaduta.

**Esempio:**

```javascript
handleAuthError();
```

---

### 2. Lettura e Formattazione Dati

``\
Legge un file JSON con contratti e restituisce i dati in formato per DataTables.

``\
Come sopra, ma con più dettagli (date, numeri univoci, ecc.).

``\
Formatta una stringa ISO in "gg/mm/aa".

**Esempio:**

```javascript
const data = await convertCdrDataToTableFormat('cdr.json');
const extended = await convertCdrDataToTableFormatExtended('cdr.json');
console.log(formatDate("2025-07-17T12:00:00Z"));
```

---

### 3. CSModalManager

``\
Gestione avanzata dei modali Bootstrap.

**Metodi:**

- `init()`
- `open()` / `close()`
- `destroy()`
- `onOpen(callback)` / `onClose(callback)`
- `onOpen_callback(callback)` / `onClose_callback(callback)` (esegue e rimuove listener dopo l’esecuzione)

**Esempio:**

```javascript
const modal = CSModalManager('#exampleModal');
modal.init();
modal.open();
modal.onClose(() => console.log("Modale chiuso"));
```

---

### 4. CSContentCopier

``\
Copia il valore dell’elemento sorgente verso destinazioni.

``\
Effettua la copia in tempo reale durante la digitazione.

**Esempio:**

```javascript
CSContentCopier.copy('#inputEmail', ['#emailPreview']);
CSContentCopier.bindLiveCopy('#inputEmail', ['#emailPreview']);
```

---

### 5. CSPasswordMeter

``\
Verifica la sicurezza della password.

**Metodi:**

- `init()`
- `getScore()`
- `reset()`

**Esempio:**

```javascript
const meter = CSPasswordMeter('#password');
meter.init();
console.log(meter.getScore());
```

---

### 6. initTooltips

``\
Inizializza tutti i tooltip Bootstrap nel documento.

**Esempio:**

```javascript
initTooltips();
```

---

### 7. Select2 Utilities

``\
Aggiunge dinamicamente opzioni a una select2.

**Esempio:**

```javascript
setDataInSelect(['admin', 'user'], '#role');
```

``\
Restituisce un array di ruoli come ID numerici.

``\
Restituisce le opzioni selezionate come array (stringhe o numeri).

**Esempio:**

```javascript
const roleIds = getSelectedOptionsRoles('roleSelect');
const texts = getSelectedOptions('selectText', 'testi');
const numbers = getSelectedOptions('selectNumbers', 'numeri');
```

``\
Carica i dati da API, li trasforma (opzionale con `mapFn`) e li applica alla select con select2. Supporta selezione predefinita.

``\
Imposta il valore solo se già presente nella select.

**Esempio completo:**

```javascript
CSSelect2Loader.init(
  '#selectUsers',
  '/api/users',
  { method: 'GET' },
  '5',
  item => ({ id: item.id, text: item.fullname }),
  { placeholder: 'Seleziona utente', allowClear: true },true
);
CSSelect2Loader.setValueIfExists('#selectUsers', '3');
```

---

### 8. FormValidatorManager

``\
Inizializza la validazione con FormValidation.js.

``\
Verifica asincrona della validità del form.

``\
Distrugge il validatore.

**Esempio:**

```javascript
FormValidatorManager.init('userForm', {
  username: {
    validators: {
      notEmpty: { message: 'Username richiesto' }
    }
  }
}, ['userRoles']);

FormValidatorManager.check('userForm').then(valid => {
  if (valid) console.log('Form valido');
});
```

---

### 9. Form Utilities

``\
Popola i campi del form dai valori in un oggetto.

``\
Resetta tutti i campi, compresi quelli `select2`.

**Esempio:**

```javascript
populateFormFields({ username: 'claudio', newsletter: true });
resetFormElements('userForm');
```

---

### 10. ToggleVisibility

``\
Mostra/nasconde alternativamente elementi specificati.

**Esempio:**

```javascript
ToggleVisibility.toggle('#viewPanel', ['#editPanel']);
```

---

### 11. Utility varie

``\
Imposta il comportamento globale delle notifiche Toastr.

``\
Restituisce un valore con 4 decimali in formato euro con virgola.

``\
Applica un ricarico percentuale al prezzo.

**Esempio:**

```javascript
toastr.success('Dati salvati con successo!');
console.log(formatEuro(23.4578)); // "23,4578"
console.log(applyMarkup(100, 15)); // 115
```

---

Tutte le funzioni qui documentate sono modulari e riutilizzabili, pensate per semplificare l'integrazione con form HTML, modali Bootstrap, select dinamiche e validazioni lato client. Se desideri, posso esportare questa guida in PDF o DOCX oppure generare una versione commentata per l'onboarding di sviluppatori.

