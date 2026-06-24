const Product = require("../models/Product");

exports.createProduct = async(req,res)=>{

    try{

        const product = await Product.create(
            req.body
        );

        res.status(201).json(product);

    }catch(error){
        res.status(500).json({
            message:error.message
        });
    }

};

exports.getProducts = async(req,res)=>{

    try{

        const products =
        await Product.find()
        .populate("farmer");

        res.json(products);

    }catch(error){

        res.status(500).json({
            message:error.message
        });

    }

};