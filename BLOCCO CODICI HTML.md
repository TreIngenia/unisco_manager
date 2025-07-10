#FORM
<div class="mb-10">
    <label for="exampleFormControlInput1" class="required form-label">Symbol in label</label>
    <input type="email" class="form-control form-control-solid" placeholder="Example input"/>
</div>

#CARD
<div class="card shadow-sm">
    <div class="card-header">
        <h3 class="card-title">Title</h3>
        <div class="card-toolbar">
            <button type="button" class="btn btn-sm btn-light">
                Action
            </button>
        </div>
    </div>
    <div class="card-body">
        Lorem Ipsum is simply dummy text...
    </div>
    <div class="card-footer">
        Footer
    </div>
</div>

#PASSWORD
<div class="fv-row mb-8" id="password" #data-kt-password-meter="true"> 
    <label for="" class="required form-label">Nuova password</label>
    <div class="mb-1">
        <div class="position-relative mb-3">
            <input class="form-control bg-transparent" type="password" placeholder="Nuova Password" name="password" autocomplete="off" />
            <span class="btn btn-sm btn-icon position-absolute translate-middle top-50 end-0 me-n2" data-kt-password-meter-control="visibility">
                <i class="fa-solid fa-eye-slash"></i>
                <i class="fa-solid fa-eye d-none"></i>
            </span>
        </div>
        <div class="d-flex align-items-center mb-3" data-kt-password-meter-control="highlight">
            <div class="flex-grow-1 bg-secondary bg-active-success rounded h-5px me-2"></div>
            <div class="flex-grow-1 bg-secondary bg-active-success rounded h-5px me-2"></div>
            <div class="flex-grow-1 bg-secondary bg-active-success rounded h-5px me-2"></div>
            <div class="flex-grow-1 bg-secondary bg-active-success rounded h-5px"></div>
        </div>
    </div>
    <div class="text-muted">Usa almeno 8 caratteri, lettere numeri e caratteri speciali.</div>
</div>