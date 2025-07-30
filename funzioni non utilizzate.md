Gestisco il controllo della complessità della password
    let CSPasswordMeter = (function () {
        let  options = {
            minLength: 8,
            checkUppercase: true,
            checkLowercase: true,
            checkDigit: true,
            checkChar: true,
            scoreHighlightClass: "active"
        };
        let passwordMeterElement = document.querySelector('#password');
        // let passwordMeterElement = document.querySelector('[name="password"]');
        let passwordMeter = null;
        return {
            init: function () {
                if (passwordMeterElement) {
                    passwordMeter = new KTPasswordMeter(passwordMeterElement, options);
                }
            },
            getScore: function () {
                return passwordMeter ? passwordMeter.getScore() : 0;
            },
            reset: function () {
                return passwordMeter ? passwordMeter.reset() : 0;
            }
        }
    })();



    let CSFormControl_user_info = (function () {
        let formElement, submitButton, validator

        return {
            init: function () {
                formElement = document.querySelector("#profile-form");
                submitButton = document.querySelector("#save_form");
                // if (!checkbox.checked) {
                //     alert("Devi accettare i termini per procedere.");
                //     return;
                // }
                // Inizializza validazione form
                validator = FormValidation.formValidation(formElement, {
                    fields: {
                        first_name: {
                            validators: {
                                notEmpty: {
                                    message: "Il nome è obbligatoria."
                                }
                            }
                        },
                        last_name: {
                            validators: {
                                notEmpty: {
                                    message: "Il cognome è obbligatoria."
                                }
                            }
                        },
                        email: {
                            validators: {
                                regexp: {
                                    regexp: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                                    message: "Inserisci un indirizzo mail valido"
                                },
                                notEmpty: {
                                    message: "L'indirizzo E-Mail è obbligatorio."
                                }
                            }
                        },
                        // actual_password: {
                        //     validators: {
                        //         notEmpty: {
                        //             message: "La password è obbligatoria."
                        //         }
                        //     }
                        // },
                        // password: {
                        //     validators: {
                        //         notEmpty: {
                        //             message: "La password è obbligatoria."
                        //         },
                        //         callback: {
                        //             message: 'Inserici una password sicura.',
                        //             callback: function (input) {
                                        
                        //                 if (input.value.length > 0) {
                        //                     return check_password.getScore() >= 25
                        //                 //     // alert(passwordMeter.getScore())
                        //                 //     return UniscoPasswordStrength.getScore() >= 50
                        //                 //     // return passwordMeter();
                        //                 }
                        //             }
                        //         }
                        //     }
                        // },
                        // confirm_password: {
                        //     validators: {
                        //         notEmpty: {
                        //             message: 'La password di conferma è obbligatoria.'
                        //         },
                        //         callback: {
                        //             message: 'Le due password non combaciano.',
                        //             callback: function (input) {
                        //                 const confirmValue = input.value;
                        //                 const passwordValue = formElement.querySelector('[name="password"]').value;

                        //                 // Mostra errore solo se l'utente ha scritto qualcosa
                        //                 if (confirmValue.length === 0) {
                        //                     return true; // Evita conflitto con notEmpty
                        //                 }

                        //                 return confirmValue === passwordValue;
                        //             }
                        //         }
                        //     }
                        // },
                        // toc: {
                        //     validators: {
                        //         notEmpty: {
                        //             message: 'Devi accettare i termini.'
                        //         }
                        //     }
                        // },
                        
                    },
                    plugins: {
                        trigger: new FormValidation.plugins.Trigger(),
                        bootstrap: new FormValidation.plugins.Bootstrap5({
                            rowSelector: ".fv-row",
                            eleInvalidClass: "",
                            eleValidClass: ""
                        })
                    }
                });

                submitButton.addEventListener("click", async function (event) {
                    event.preventDefault();

                    const status = await validator.validate();
                    if (status === "Valid") {
                        submitButton.setAttribute("data-kt-indicator", "on");
                        submitButton.disabled = true;

                        const form = document.getElementById('profile-form');
                        const formData = new FormData(form);
                        const data = Object.fromEntries(formData.entries());

                        let response = await aggiorna_dati(data);

                        submitButton.setAttribute("data-kt-indicator", "off");
                        submitButton.disabled = false;

                        if (response) {
                            Swal.fire({
                                text: response.message,
                                icon: response.status,
                                buttonsStyling: false,
                                confirmButtonText: "Ok, riprovo!",
                                timer: 2000,
                                timerProgressBar: true,
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            }).then((result) => {
                                if(response.status == 'success'){
                                CSTabManager.saveState();
                                location.reload();
                                // formElement.querySelectorAll("input, select, textarea").forEach(el => {
                                //     if (el.type === "checkbox" || el.type === "radio") {
                                //         el.checked = false;
                                //     } else {
                                //         el.value = "";
                                //     }
                                // });
                                // modal_password.close();
                            }
                            })
                            
                        }

                        // if (response.status === 'success') {
                        //     let userId = data.user.id;
                            
                        //     // 2. Upload immagine se presente (FormData separato)
                        //     const imageFile = document.getElementById('profile-image').files[0];
                        //     if (imageFile) {
                        //         const avatarUrl = await uploadUserImage(userId, imageFile);
                        //         if (avatarUrl) {
                        //             console.log('Immagine caricata:', avatarUrl);
                        //         }
                        //     }
                            
                        //     alert(data.message);
                        //     return data
                        //     closeUserModal();
                        //     reloadUsers();
                        // } else {
                        //     alert(data.message || 'Errore nel salvataggio');
                        //     return data
                        // }
                    }
                });
            }
        };
    })();