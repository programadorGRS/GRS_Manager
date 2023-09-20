async function fetchOpcoesEmpPrinc(endpoint, idcampoEmpPrinc, idCampoAlvo, idCampoAtivos = null){
    // atualiza campo select "campoAlvo" de acordo com a response da API

    let codEmpPrinc = document.getElementById(idcampoEmpPrinc).value;

    let campoAlvo = document.getElementById(idCampoAlvo);

    if (codEmpPrinc == "") {
        campoAlvo.innerHTML = '<option value="">Selecione uma Empresa Principal</option>';
        return null
    }

    // filtro para entidades ativas ou inativas (opcional)
    let ativos = null;
    if (idCampoAtivos){
        ativos = document.getElementById(idCampoAtivos).value;
    }

    // call API
    let respJson = null;
    try{
        const queryParams = {"cod_emp_princ": codEmpPrinc, "ativo": ativos}
        respJson = await callAPI(endpoint, queryParams)
    } catch (err) {
        console.error(err);
        return null
    }

    // updated field options
    if (respJson){
        campoAlvo.innerHTML = getOptsFromJsonData(respJson);
    }
}


async function fetchOpcoesEmpresa(endpoint, idcampoEmpresa, idCampoAlvo, idCampoAtivos = null){
    // atualiza campo select "campoAlvo" de acordo com a response da API

    let codEmpresa = document.getElementById(idcampoEmpresa).value;

    let campoAlvo = document.getElementById(idCampoAlvo);

    if (codEmpresa == "") {
        campoAlvo.innerHTML = '<option value="">Selecione uma Empresa</option>';
        return null
    }

    // filtro para entidades ativas ou inativas (opcional)
    let ativos = null;
    if (idCampoAtivos){
        ativos = document.getElementById(idCampoAtivos).value;
    }

    // call API
    let respJson = null;
    try {
        const queryParams = {"id_empresa": codEmpresa, "ativo": ativos}
        respJson = await callAPI(endpoint, queryParams)
    } catch (err) {
        console.error(err);
        return null
    }

    // updated field options
    if (respJson){
        campoAlvo.innerHTML = getOptsFromJsonData(respJson);
    }
}


async function callAPI(endpoint, queryParams){
    // queryParams must be json object
    const URLparams = new URLSearchParams(queryParams);

    const resp = await fetch(endpoint + "?" + URLparams);

    return await resp.json()
}


function getOptsFromJsonData(jsonData){
    let optionHTML = '<option value="">Selecione</option>';

    for (let opt of jsonData) {
        optionHTML += '<option value="' + opt.id + '">' + opt.nome + '</option>';
    }

    return optionHTML
}