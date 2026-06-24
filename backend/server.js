const express = require("express");
const mongoose = require("mongoose");
require("dotenv").config();

const app = express();

app.use(express.json());

app.use(
 "/api/auth",
 require("./routes/auth")
);

app.use(
 "/api/products",
 require("./routes/products")
);

mongoose.connect(
 process.env.MONGO_URI
)
.then(()=>{

    app.listen(5000,()=>{

        console.log(
          "Server running on port 5000"
        );

    });

});