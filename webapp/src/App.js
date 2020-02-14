// import 'bootswatch/dist/lux/bootstrap.min.css';
// import "./assets/css/index.css"

// import React, { useState, useEffect } from 'react';
// import { Route, Switch, BrowserRouter } from "react-router-dom";
// import 'datejs';
// import jwtDecode from 'jwt-decode';
// import LinkedAccountContext from "./context/LinkedAccountContext";
// import LinkedAccountState from "./context/LinkedAccountState";

// //core components
// import Home from "./Home/Home";
// import Navbar from "./Navbar/Navbar";
// import Auth from "./Auth";
// import Form from "./LinkedAccount/Schema";


// const App = () => {
//   const [user, setUser] = useState(_setUser(true));
//   const { providersList } = LinkedAccountContext;

//   useEffect(() => {
//     _setUser();
//   }, []);

//   function _resetUser() {
//     console.log("in reset user")
//     setUser({ user: null });
//   }

//   //hardcode token for now as long as no token from serverside available
//   function _setUser(init) {
//     const token = localStorage.getItem('identity');
//     if (token) {
//       console.log({ token })
//       // const decoded = jwtDecode(token)
//       // console.log({ decoded })
//       // delete decoded.iat
//       // if (init) return decoded
//       if (init) return token;
//       // setUser({ user: decoded })
//       setUser({ user: token })
//     } else {
//       return null;
//     }
//   }

//   return (
//     <LinkedAccountState>
//       <BrowserRouter>
//         <div>
//           <Navbar user={user} providers={providersList} />
//           <Switch>
//             <Route exact path="/" render={() => <Home user={user} />} />
//             <Route path="/auth" render={() => <Auth setUser={_setUser} resetUser={_resetUser} />} />
//             <Route path="/linked-account" render={() => <Form providers={providersList} />} />
//             {/* <Route component={Error}/> */}
//           </Switch>
//         </div>
//       </BrowserRouter>
//     </LinkedAccountState>
//   )
// }

// export default App;



import 'bootswatch/dist/lux/bootstrap.min.css';
import "./assets/css/index.css"
import { ToastContainer, Slide } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import React, { useEffect, useState } from 'react';
import { Route, Switch, BrowserRouter } from "react-router-dom";
import 'datejs';
import AuthState from "./context/AuthState";
import LinkedAccountState from "./context/LinkedAccountState";
import AlertState from './context/AlertState';
import Alert from "./components/Alerts";

//core components
import Home from "./Home/Home";
import Navbar from "./Navbar/Navbar";
import Auth from "./Auth";
import Form from "./LinkedAccount/Schema";
import LinkedAccount from "./LinkedAccount";

const App = () => {
  //  const [user, setUser] = useState(localStorage.getItem("identity"));

  // useEffect(() => {
  //   if (localStorage.getItem("identity")) {
  //     setUser(localStorage.item)
  //   } else {
  //     setUser(null)
  //   }
  // }, [])


  return (
    <AuthState>
      <LinkedAccountState>
        <AlertState>
          <BrowserRouter>
            <div>
              <Navbar />
              <ToastContainer autoClose={4000} transition={Slide} position="bottom-right" />
              <Alert />
              <Switch>
                <Route exact path="/" render={() => <Home />} />
                <Route path="/auth" render={() => <Auth />} />
                <Route path="/linked-account" render={() => <LinkedAccount />} />
                {/* <Route component={Error}/> */}
              </Switch>
            </div>
          </BrowserRouter>
        </AlertState>
      </LinkedAccountState>
    </AuthState>
  )
}

export default App;
