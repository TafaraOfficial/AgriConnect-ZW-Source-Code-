const Product = require("../models/Product");

exports.dashboardStats = async(req,res)=>{

    try{

        const totalProducts =
        await Product.countDocuments();

        const totalQuantity =
        await Product.aggregate([
          {
            $group:{
                _id:null,
                total:{
                    $sum:"$quantity"
                }
            }
          }
        ]);

        res.json({

            totalProducts,

            totalQuantity:
            totalQuantity[0]?.total || 0

        });

    }catch(error){

        res.status(500).json({
            message:error.message
        });

    }

};