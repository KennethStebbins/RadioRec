function wait(millis) {
    return new Promise(resolve => {
        setTimeout(resolve, millis);
    });
}

async function getStreamingURL(regex = /KMGLFMAAC\.aac/) {
    let btnPlay = document.getElementById('playButton');
    let btnStop = document.getElementById('stopButton');

    btnPlay.click();

    await wait(3000);

    btnStop.click();

    await wait(1000);

    let performanceEntries = window.performance.getEntries();
    let matchedItem = null;
    for(let i = 0; i < performanceEntries.length; i++) {
        let entry = performanceEntries[i];

        if(entry.name.match(regex)) {
            matchedItem = entry;
            break;
        }
    }

    return matchedItem.name;
}

getStreamingURL().then(url => console.log(url));
