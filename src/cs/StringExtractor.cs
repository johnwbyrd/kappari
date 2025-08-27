using System;
using System.Reflection;
using System.IO;

class Program
{
    static void Main(string[] args)
    {
        try
        {
            Console.WriteLine("Paprika String Extractor");
            Console.WriteLine("========================");
            
            // Path to Paprika executable
            string paprikaPath = @"c:\Temp\cleaned.exe";
            
            // Check if file exists
            if (!File.Exists(paprikaPath))
            {
                Console.WriteLine("Paprika not found at: " + paprikaPath);
                Console.WriteLine("Please update the path in the source code.");
                return;
            }
            
            Console.WriteLine("Loading assembly: " + paprikaPath);
            
            // Load the Paprika assembly
            Assembly asm = Assembly.LoadFrom(paprikaPath);
            Console.WriteLine("Assembly loaded successfully");
            
            // Get the Class158 type
            Type class158 = asm.GetType("Class158");
            if (class158 == null)
            {
                Console.WriteLine("ERROR: Could not find Class158 type");
                return;
            }
            
            Console.WriteLine("Found Class158 type");
            
            // Get the smethod_0 static method
            MethodInfo smethod0 = class158.GetMethod("smethod_0", BindingFlags.Static | BindingFlags.Public);
            if (smethod0 == null)
            {
                Console.WriteLine("ERROR: Could not find smethod_0 method");
                return;
            }
            
            Console.WriteLine("Found smethod_0 method");
            Console.WriteLine();
            
            // Extract the encryption keys we need for license decryption
            Console.WriteLine("Extracting license encryption keys...");
            
            try
            {
                string key53460 = (string)smethod0.Invoke(null, new object[] { 53460 });
                Console.WriteLine("Key 53460 (data encryption): '" + key53460 + "'");
            }
            catch (Exception ex)
            {
                Console.WriteLine("ERROR getting key 53460: " + ex.Message);
            }
            
            try
            {
                string key53414 = (string)smethod0.Invoke(null, new object[] { 53414 });
                Console.WriteLine("Key 53414 (signature encryption): '" + key53414 + "'");
            }
            catch (Exception ex)
            {
                Console.WriteLine("ERROR getting key 53414: " + ex.Message);
            }
            
            // Also extract the key for the null check in GClass1
            Console.WriteLine();
            Console.WriteLine("Extracting null check key...");
            
            try
            {
                string key34702 = (string)smethod0.Invoke(null, new object[] { 34702 });
                Console.WriteLine("Key 34702 (null check): '" + key34702 + "'");
            }
            catch (Exception ex)
            {
                Console.WriteLine("ERROR getting key 34702: " + ex.Message);
            }
            
            // Extract keys needed for public key extraction
            Console.WriteLine();
            Console.WriteLine("Extracting public key related strings...");
            
            int[] publicKeyIndices = { 16875, 20393, 19815, 16957, 20393, 16875 };
            
            foreach (int index in publicKeyIndices)
            {
                try
                {
                    string value = (string)smethod0.Invoke(null, new object[] { index });
                    Console.WriteLine("Index " + index + ": '" + value + "'");
                }
                catch (Exception ex)
                {
                    Console.WriteLine("Index " + index + ": ERROR - " + ex.Message);
                }
            }
            
            // Extract additional potentially useful strings
            Console.WriteLine();
            Console.WriteLine("Extracting additional useful strings...");
            
            int[] additionalIndices = { 8887, 19824, 19793, 17015, 16978, 16938, 16903 };
            
            foreach (int index in additionalIndices)
            {
                try
                {
                    string value = (string)smethod0.Invoke(null, new object[] { index });
                    Console.WriteLine("Index " + index + ": '" + value + "'");
                }
                catch (Exception ex)
                {
                    Console.WriteLine("Index " + index + ": ERROR - " + ex.Message);
                }
            }
            
        }
        catch (Exception ex)
        {
            Console.WriteLine("FATAL ERROR: " + ex.Message);
            Console.WriteLine("Stack trace: " + ex.StackTrace);
        }
    }
}