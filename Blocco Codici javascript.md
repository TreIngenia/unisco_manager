let CSModalManager = (function () {
    let modalElement = document.querySelector('#modal_change_password');
    let modalInstance = null;
    let option = {
        keyboard: false,
        backdrop: true
    }
    return {
        init: function () {
            if (modalElement) {
                modalInstance = new bootstrap.Modal(modalElement, option);
            }
        },
        open: function () {
            if (modalInstance) {
                modalInstance.show();
            }
        },
        close: function () {
            if (modalInstance) {
                modalInstance.hide();
            }
        },
        onClose: function (callback) {
            if (modalElement) {
                modalElement.addEventListener('hidden.bs.modal', function () {
                    if (typeof callback === 'function') {
                        callback();
                    }
                });
            }
        },
        onOpen: function (callback) {
            if (modalElement) {
                modalElement.addEventListener('shown.bs.modal', function () {
                    if (typeof callback === 'function') {
                        callback();
                    }
                });
            }
        }
    };
})();

    function CSModalManager(selector) {
        let modalElement = document.querySelector(selector);
        let modalInstance = null;
        let options = {
            keyboard: false,
            backdrop: true
        };

        return {
            init: function () {
                if (modalElement) {
                    modalInstance = new bootstrap.Modal(modalElement, options);
                }
            },
            open: function () {
                if (modalInstance) {
                    modalInstance.show();
                }
            },
            close: function () {
                if (modalInstance) {
                    modalInstance.hide();
                }
            },
            onClose: function (callback) {
                if (modalElement) {
                    modalElement.addEventListener('hidden.bs.modal', function () {
                        if (typeof callback === 'function') {
                            callback();
                        }
                    });
                }
            },
            onOpen: function (callback) {
                if (modalElement) {
                    modalElement.addEventListener('shown.bs.modal', function () {
                        if (typeof callback === 'function') {
                            callback();
                        }
                    });
                }
            }
        };
    }