const downloadBtn = document.querySelector('.download__button');
const url_input = document.querySelector('.url__input');
const append_data = document.querySelector('.append__data');
const img_thumbnail = document.querySelector('.thumbnail');
const title_time = document.querySelector('.title-time');


downloadBtn.addEventListener('click', function () {
    console.log("Catched:", url_input.value);
    append_data.innerHTML = '';
    sendURL((url_input.value).toString());
});


function sendURL(URL){
    //console.log("Catched 222:", URL, typeof(URL));
    fetch(`http://localhost:4000/download?URL=${URL}`,{
        method: 'GET',
        mode: 'cors'
    }).then((response) => {
        //console.log(response.json());
        return response.json();
    }).then((data) => {
        console.log(JSON.parse(data));
        for( let i in JSON.parse(data)){
            console.log(JSON.parse(data)[i]);
            let tr = document.createElement("tr");
            let hasSound = "";
            JSON.parse(data)[i]['codecs'].includes(',') ||  JSON.parse(data)[i]['qualityLabel'] == null ? hasSound = "&#x1F50A" : hasSound = "&#x1F507";
                tr.innerHTML = `
                <tr>
                <td title=\"Codec: ${JSON.parse(data)[i]['codecs']}\">
                ${hasSound} ${JSON.parse(data)[i]['qualityLabel'] == null? "audio" : JSON.parse(data)[i]['qualityLabel']}
                <p>${JSON.parse(data)[i]['codecs']}</p>
                </td>
                <td tittle="Кодеки ">${(JSON.parse(data)[i]['contentLength']/1024/1024).toFixed(2)}МB</td>
                <td>⬇️ Download</td>
                </tr>
                `;
                
                append_data.appendChild(tr);
            
                img_thumbnail.setAttribute("src",`http://img.youtube.com/vi/${JSON.parse(data)[i]['videoId']}/hqdefault.jpg`);
                title_time.innerHTML = `${JSON.parse(data)[i]['title']}<br>🎬Duration: ${(JSON.parse(data)[i]['lengthSeconds']/60).toFixed(2).toString().replace(".",":")}`;


        }
        



    });
}