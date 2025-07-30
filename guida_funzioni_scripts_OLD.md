**Guida all'Uso delle Funzioni nel file **``

---

### 1. API Globale

`` Effettua una chiamata `fetch` con configurazione standard per le API. Gestisce sessioni scadute e messaggi di errore.

**Esempio:**

```javascript
const result = await apiCall('/admin/api/users', { method: 'GET' });
```

`` Mostra un alert e reindirizza al login in caso di sessione scaduta.

**Esempio:**

```javascript
handleAuthError();
```

---

### 2. Lettura e Formattazione Dati

`` Legge un file JSON con contratti e restituisce i dati in formato per DataTables.

**Esempio:**

```javascript
const data = await convertCdrDataToTableFormat('cdr.json');
```

`` Come sopra, ma con più dettagli (date, numeri univoci, ecc.).

**Esempio:**

```javascript
const data = await convertCdrDataToTableFormatExtended('cdr.json');
```

`` Formatta una stringa ISO in "gg/mm/aa".

**Esempio:**

```javascript
formatDate("2025-07-17T12:00:00Z"); // "17/07/25"
```

---

### 3. Modale Bootstrap

`` Gestione avanzata di modali Bootstrap.

**Esempio:**

```javascript
const modal = CSModalManager('#myModal');
modal.init();
modal.open();
```

---

### 4. Copia Contenuti

`` Copia il contenuto da un campo sorgente a uno o più campi destinazione.

**Esempio:**

```javascript
CSContentCopier.copy('#email', ['#username', '#display_email']);
```

`` Attiva la copia automatica durante la digitazione.

**Esempio:**

```javascript
CSContentCopier.bindLiveCopy('#email', ['#username']);
```

---

### 5. Password Meter

`` Inizializza e gestisce un misuratore di sicurezza password.

**Esempio:**

```javascript
const meter = CSPasswordMeter('#passwordInput');
meter.init();
console.log(meter.getScore());
```

---

### 6. Tooltip Bootstrap

`` Inizializza tutti i tooltip presenti nel DOM.

**Esempio:**

```javascript
initTooltips();
```

---

### 7. Select2 Utility

`` Popola dinamicamente una select2.

**Esempio:**

```javascript
setDataInSelect(['admin', 'user'], '#roleSelect');
```


`` Restituisce i valori selezionati convertiti in ID ruolo.

**Esempio:**

```javascript
const roles = getSelectedOptionsRoles('roleSelect');
```

`` Restituisce valori selezionati: testo o numero.

**Esempio:**

```javascript
const selectedTexts = getSelectedOptions('tags', 'testi');
const selectedNumbers = getSelectedOptions('ids', 'numeri');
```


`` Carica dati da API e inizializza una Select2.

**Esempio:**

```javascript
CSSelect2Loader.init('#selectClienti', '/api/clients');

CSSelect2Loader.init('#mySelect', '/api/companies', {}, 2);

CSSelect2Loader.init('#mySelect', '/api/companies', {}, null, item => ({
    id: item.uid,
    text: `${item.name} (${item.e_mail})`
}));

CSSelect2Loader.init('#mySelect', '/api/companies', {}, null, null, {
    placeholder: 'Seleziona una società',
    allowClear: true,
    minimumResultsForSearch: 5
});

```


`` Se il valore esiste, lo seleziona.

**Esempio:**

```javascript
CSSelect2Loader.setValueIfExists('#selectClienti', '3');
```

---

### 8. Validazione Form

`` Modulo per la validazione.

**Esempio:**

```javascript
FormValidatorManager.init('myForm', {
  email: {
    validators: {
      notEmpty: { message: 'Email richiesta' },
      emailAddress: { message: 'Email non valida' }
    }
  }
});

const isValid = await FormValidatorManager.check('myForm');
```

---

### 9. Utility Form

`` Popola un form con i valori passati.

**Esempio:**

```javascript
populateFormFields({ email: 'test@example.com', active: true });
```

`` Resetta tutti i campi del form.

**Esempio:**

```javascript
resetFormElements('myForm');
```

---

### 10. Toggle Visibilità

`` Nasconde e mostra elementi alternandoli.

**Esempio:**

```javascript
ToggleVisibility.toggle('#viewMode', ['#editMode']);
```

---

### 11. Altre Utility

`` Configurazione notifiche `toastr`.

**Esempio:**

```javascript
toastr.success('Operazione completata!');
```

`` Formatta un numero come valore euro.

**Esempio:**

```javascript
formatEuro(12.3456); // "12,3456"
```

`` Calcola un prezzo con ricarico.

**Esempio:**

```javascript
applyMarkup(100, 25); // 125
```

