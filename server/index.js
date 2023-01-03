const express = require('express');
const cors = require('cors');
const path = require('path');
const ytdl = require('ytdl-core');
const fs = require('fs');
const urlLib = require('url');
const https = require('https');
const app = express();


app.use(express.static(process.cwd()));

app.listen(4000, () =>{
    console.log('Server is running at 4000 port');

});

function getContentlength(url, itag){
    let promise = new Promise((resolve, reject) => {
        const video = ytdl(url, { filter: format => format.itag === parseInt(itag), range: { start: 0, end: 1000 } });
        video.on('info', (info, format) => {
        let parsed = urlLib.parse(format.url);
        parsed.method = 'HEAD';
        https.request(parsed, (res) => {
            //console.log('total length:', res.headers['content-length'], typeof(res.headers['content-length']));
            resolve(res.headers['content-length']);
            
            }).end();        
            });
        }); 
        return promise;
} 
// (async () => {
//     data = await getContentlength('https://www.youtube.com/watch?v=OPNBWaBZvjc', 18);
// console.log("OOPs:",data );
// })();
// ytdl('https://www.youtube.com/watch?v=OPNBWaBZvjc', { filter: format => format.itag === 22 })
//     .pipe(fs.createWriteStream('video.mp4'));


app.get('/download', cors(), (req, res) => {
    let URL = (req.query.URL).toString();
    console.log("Get it:", URL);
    let cool = ytdl.getInfo(URL, { filter: format => format.container === 'mp4' })
    let video_info = {}


cool.then( result =>{
    //console.log(result);
    for (let i = 0; i < result.formats.length; i++) {
        if (result.formats[i].container === 'mp4') {
            video_info[i] = i;
            video_info[i] = {};
            video_info[i]["title"] = result.videoDetails["title"];
            video_info[i]["lengthSeconds"] = result.videoDetails["lengthSeconds"];
            video_info[i]["videoId"] = result.videoDetails["videoId"];
            video_info[i]["itag"] = result.formats[i].itag;
            video_info[i]["container"] = result.formats[i].container;
            video_info[i]["qualityLabel"] = result.formats[i].qualityLabel;
            if(!result.formats[i].contentLength){
            
                async () => {
                    video_info[i]["contentLength"] = await getContentlength(URL, result.formats[i].itag);
                    //console.log("Have contact>>>", video_info[i]["contentLength"]);
                }
               // console.log(`get it>>> ${video_info[i]["qualityLabel"]}`, video_info[i]["contentLength"]);
                
            }else{
                //console.log("get it!", result.formats[i].contentLength );
                video_info[i]["contentLength"] = result.formats[i].contentLength;
            }
            video_info[i]["codecs"] = result.formats[i].codecs;
        }

    }
        
        res.json(JSON.stringify(video_info));
});
}); 

app.get('/', (req, res) => {
    res.sendFile(path.join(process.cwd(),'index.html'))
});

// app.get('/download', cors(), (req, res) => {
//     let URL = req.query.URL;
//     console.log(URL);
//     res.json({});
// }); 

/**
res.header('Content-Disposition', 'attachment; filename="video.mp4"');
ytdl(URL,{
    format: 'mp4'
}).pipe(res);
*/
