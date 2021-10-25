/*function printData() {
    var divToPrint=document.getElementById("mainContainer");

    newWin= window.open("");

    newWin.document.write(divToPrint.outerHTML);

    newWin.print();

    newWin.close();
}

setTimeout(function mainFunction(){
    try {
        document.getElementById("run").addEventListener("click", function(){
            printData();
        })
      }
      catch(err) {
        console.log(err)
      }
    console.log('Listener Added!');
}, 30000);*/

function createPDF(){

	var jQueryScript2 = document.createElement('script'); 
	jQueryScript2.setAttribute('src','http://127.0.0.1:8050/assets/html2canvas.js');
	document.head.appendChild(jQueryScript2);
	var jQueryScript3 = document.createElement('script'); 
	jQueryScript3.setAttribute('src','http://127.0.0.1:8050/assets/jsPDF.js');
	document.head.appendChild(jQueryScript3);
	
	const printArea = document.getElementById("mainContainer");

	html2canvas(printArea, {scale:3}).then(function(canvas){						
		var imgData = canvas.toDataURL('image/png');
		var doc = new jsPDF('l', 'mm', "a4");
		
		const pageHeight = doc.internal.pageSize.getHeight();
		const imgWidth = doc.internal.pageSize.getWidth();
		var imgHeight = canvas.height * imgWidth / canvas.width;
		var heightLeft = imgHeight;
		
		
		var position = 10; // give some top padding to first page

		doc.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
		heightLeft -= pageHeight;

		while (heightLeft >= 0) {
		  position += heightLeft - imgHeight; // top padding for other pages
		  doc.addPage();
		  doc.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
		  heightLeft -= pageHeight;
		}
		//doc.autoPrint({variant: 'non-conform'});
		doc.save( 'file2.pdf');
		//doc.output('blob', 'file.pdf')
		window.open(doc.output('bloburl'))
	})
}

setTimeout(function mainFunction(){
	try {
		document.getElementById("run").addEventListener("click", function(){
			createPDF();
		})
	}
	catch(err) {
		console.log(err)
	}
	console.log('Listener Added2!');
}, 30000);
