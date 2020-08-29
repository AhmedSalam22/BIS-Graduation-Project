const num = document.querySelector("#inputNumber");
const myCustomDiv = document.createElement('div');
const myCustomDiv2 = document.createElement('div');
const table = document.querySelector('#pixelCanvas');
const result = document.querySelector("#Result");
const form = document.querySelector("#PartnersNumber");


function total(capitl){
    
}

function responseToSubmit(){
    event.preventDefault()
    let num = document.querySelector("#inputNumber");
    let capitl = document.querySelectorAll(".inputs")
    let method = document.querySelector("#method")
    var x = 0
    capitl.forEach(function(element) { x = x + Number(element.value) ; return x})

    let percentage  = document.querySelectorAll(".percentage")
    myCustomDiv2.innerHTML = "";

    let investment_in_partnership = Number(capitl[0].value)
    var sumCapitalForOldPartner = x - Number(capitl[0].value)

    console.log("x: " + x + "investment_in_partnership: "+ investment_in_partnership + "ldP: "+ sumCapitalForOldPartner)
    let bookvalue = sumCapitalForOldPartner  * Number(percentage[0].value)
    console.log(bookvalue)
    const p = document.createElement("p")
    console.log(investment_in_partnership -  bookvalue)
    console.log(investment_in_partnership -  bookvalue == 0)
    

    
    if (investment_in_partnership -  bookvalue == 0) {
                p.innerHTML = "Cash debit by: " + investment_in_partnership + "<br>" + "New partner's Capital Credit by: " + investment_in_partnership
                myCustomDiv2.appendChild(p) 
                console.log(p)
    } else {
        if (method.value == "Bouns" && investment_in_partnership > bookvalue ) {
            p.innerHTML =  "Cash debit by: " + investment_in_partnership + "<br>" + "New partner's Capital Credit by: " + bookvalue + "<br>"
            for (var x = 1 ;  x < Number(num.value) ; x++) {
                p.innerHTML = p.innerHTML + "partner " + (x + 1) + "Credit by: " + (investment_in_partnership -  bookvalue) * Number(percentage[x].value) + "<br>"
                myCustomDiv2.appendChild(p) 
                console.log(p)
            } 
        } else if (method.value == "Good will" && investment_in_partnership > bookvalue ) {
            let impliedGoodWill = (investment_in_partnership / Number(percentage[0].value )) -  sumCapitalForOldPartner
            p.innerHTML =  "Cash debit by: " + investment_in_partnership + "<br>" + "New partner's Capital Credit by: " + investment_in_partnership + "<br>"
            p.innerHTML = p.innerHTML + "Good will Debit by: " + impliedGoodWill + "<br>" 
            for (var x = 1 ;  x < Number(num.value) ; x++) {
                p.innerHTML = p.innerHTML + "partner " + (x + 1) + "Credit by: " + (impliedGoodWill) * Number(percentage[x].value) + "<br>"
                myCustomDiv2.appendChild(p) 
                console.log(p)
            }
    }  else if (method.value == "Bouns" && investment_in_partnership < bookvalue ){
        p.innerHTML =  "Cash debit by: " + investment_in_partnership + "<br>" + "New partner's Capital Credit by: " + bookvalue + "<br>"
        for (var x = 1 ;  x < Number(num.value) ; x++) {
            p.innerHTML = p.innerHTML + "partner " + (x + 1) + "Credit by: " + ( bookvalue - investment_in_partnership) * Number(percentage[x].value) + "<br>"
            myCustomDiv2.appendChild(p) 
            console.log(p) }

    } else if (method.value == "Good will" && investment_in_partnership < bookvalue) {
        let impliedGoodWill =  (sumCapitalForOldPartner - investment_in_partnership ) / (1- Number(percentage[0].value) )  - sumCapitalForOldPartner
        p.innerHTML =  "Cash debit by: " + investment_in_partnership + "<br>" + "New partner's Capital Credit by: " + investment_in_partnership + "<br>"
        p.innerHTML = p.innerHTML + "Good will Debit by: " + impliedGoodWill + "<br>" 
        myCustomDiv2.appendChild(p) 

    }

}

    result.appendChild(myCustomDiv2)
    

    
};

function responseToInput(){
    let num = document.querySelector("#inputNumber")
    myCustomDiv.innerHTML = "";
    for (var row = 1 ; row <= (num.value * 2)  ; row++){
        const tr = document.createElement('tr');
        myCustomDiv.appendChild(tr)
        console.log("test")
        for(var column = 1 ; column <= 2 ; column++){
            const td = document.createElement('td');
            if (column == 1 && row % 2 === 0) {
                td.innerText = "percentage %  " + "for partner " + (row / 2) 
            } else if (column == 1 && row % 2 !== 0) {
                td.innerText = "Investment /Capital  " + "for partner " + ((row + 1) / 2) 
            } else if (column == 2 && row % 2 === 0){
                td.innerHTML = "<input type='number' class='percentage'>"
            } else {
                td.innerHTML = "<input type='number' class='inputs'>"
            }
            
    
    
            myCustomDiv.lastChild.appendChild(td)
    
        }
      }
      event.preventDefault();
}


table.appendChild(myCustomDiv);

num.addEventListener("input"  , responseToInput);
form.addEventListener("submit" , responseToSubmit);
