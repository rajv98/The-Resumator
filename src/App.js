import React, { Component } from 'react';

import './App.css';
import logo from './logo.jpg';

class App extends Component {

   
    // fetches returned value from Flask endpoint
    //calls pythons script
    fetchIndexer() {
        console.log("fetching python localhost");
        
        fetch('http://localhost:5000/', {
            method: 'GET',

            dataType: 'json'
        })
            .then(r => r.json())
            .then(r => {
                console.log(r);

                let obj = Object.entries(r);
                document.getElementById("root").innerHTML += "Best matches for Manager, Service Management <br></br>";
                document.getElementById("root").innerHTML += "Candidate Number , Match Percentage<br></br>";
                for (let prop in obj) {
                    document.getElementById("root").innerHTML += obj[prop] +" <br></br>";
                }
            })
            .catch(err => console.log(err))


       
    }


    
    //react render method, renders the html page
  render() {
    return (
        <div className="App">
          
            <header className="App-header">
                
                <h1 className="App-title">Welcome to Resumator!</h1>
                This application takes a resume, and returns the best matching job titles.
    
            </header>
            <p className="App-intro"> 
                To add a resume to the database, upload the file below (pdf)<br></br>
                <input type="file" name="pic" />
                <button>RESUMATE</button><br></br><br></br><br></br>
                
                To search for best candidates, enter job title below<br></br>
                <input type="text" id="person" placeholder="Manager, Service Management"/>

                <button onClick={this.fetchIndexer}>Search</button><br></br>
           
    
            </p>

   
          
      </div>
    );
  }
}

    

export default App;
