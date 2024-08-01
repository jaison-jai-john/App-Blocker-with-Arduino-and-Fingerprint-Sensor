#include <Adafruit_Fingerprint.h>


#if (defined(__AVR__) || defined(ESP8266)) && !defined(__AVR_ATmega2560__)
// For UNO and others without hardware serial, we must use software serial...
// pin #2 is IN from sensor (GREEN wire)
// pin #3 is OUT from arduino  (WHITE wire)
// Set up the serial port to use softwareserial..
SoftwareSerial mySerial(2, 3);

#else
// On Leonardo/M0/etc, others with hardware serial, use hardware serial!
// #0 is green wire, #1 is white
#define mySerial Serial1

#endif

// make finger object
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

// will hold the op choice
uint8_t op;

void setup() {
  // set baude rate
  Serial.begin(9600);
  // wait till Serial has started
  while(!Serial);
  // to not overload cpu
  delay(100);

  // set the data rate for the sensor serial port
  finger.begin(57600);

  while(!finger.verifyPassword()){
    Serial.println("Did not find sensor!");
    delay(1);
  }

  Serial.println("sensor found and online!");

  Serial.println(F("Reading sensor parameters"));
  finger.getParameters();
  Serial.print(F("Status: 0x")); Serial.println(finger.status_reg, HEX);
  Serial.print(F("Sys ID: 0x")); Serial.println(finger.system_id, HEX);
  Serial.print(F("Capacity: ")); Serial.println(finger.capacity);
  Serial.print(F("Security level: ")); Serial.println(finger.security_level);
  Serial.print(F("Device address: ")); Serial.println(finger.device_addr, HEX);
  Serial.print(F("Packet len: ")); Serial.println(finger.packet_len);
  Serial.print(F("Baud rate: ")); Serial.println(finger.baud_rate);
}

uint8_t readNumber(void){
  uint8_t num = 0;
  while (num == 0) {
    while (! Serial.available());
    num = Serial.parseInt();
  }
  return num;
}

uint8_t getFingerPrint(int slot = 1){
  int p = -1;
  while(1){
    Serial.println("Place finger");
    while (p != FINGERPRINT_OK){
      p = finger.getImage();
      switch (p) {
      // fingerprin taken
      case FINGERPRINT_OK:
        Serial.println("Image taken");
        break;
      // finger not found
      case FINGERPRINT_NOFINGER:
        Serial.println(".");
        break;
      // packet loss
      case FINGERPRINT_PACKETRECIEVEERR:
        Serial.println("Communication error");
        break;
      // error processing image
      case FINGERPRINT_IMAGEFAIL:
        Serial.println("Imaging error");
        break;
      // unknown error
      default:
        Serial.println("Unknown error");
        break;
      }
    }

    // convert image
    p = finger.image2Tz(slot);
    switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image converted");
      return p;
    case FINGERPRINT_IMAGEMESS:
      Serial.println("Image too messy");
    case FINGERPRINT_PACKETRECIEVEERR:
      Serial.println("Communication error");
    case FINGERPRINT_FEATUREFAIL:
      Serial.println("Could not find fingerprint features");
    case FINGERPRINT_INVALIDIMAGE:
      Serial.println("Could not find fingerprint features");
    default:
      Serial.println("Unknown error");
    }
  }
}

void addFinger(void){
  // get fingerprint ID
  Serial.println("Enter finger print id from 1 to 127");
  uint8_t id = readNumber();
  // initialize variable for holding temp values
  uint8_t p;
  // id cannot be 0
  if(id == 0){
    Serial.print("Id cannot be 0");
    return;
  }

  while(1){
    while(1){
      // get fingerprint
      getFingerPrint(1);
      // take fingerprint again
      Serial.println("Remove finger");
      delay(2000);
      getFingerPrint(2);

      // create model and match prints
      p = finger.createModel();
      if (p == FINGERPRINT_OK) {
        Serial.println("Prints matched!");
        break;
      } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
        Serial.println("Communication error");
      } else if (p == FINGERPRINT_ENROLLMISMATCH) {
        Serial.println("Fingerprints did not match");
      } else {
        Serial.println("Unknown error");
      }
    }
    
    // store model
    p = finger.storeModel(id);
    if (p == FINGERPRINT_OK) {
      Serial.println("Stored!");
      return;
    } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
      Serial.println("Communication error");
    } else if (p == FINGERPRINT_BADLOCATION) {
      Serial.println("Could not store in that location");
    } else if (p == FINGERPRINT_FLASHERR) {
      Serial.println("Error writing to flash");
    } else {
      Serial.println("Unknown error");
    }
  }
}


void removeFinger(void){
  Serial.println("Enter Id of the fingerprint that is to be deleted: ");
  uint8_t id = readNumber();
  if(id == 0){
    return;
  }

  Serial.print("Deleteing ID #"); Serial.println(id);

  uint8_t p = -1;

  p = finger.deleteModel(id);

  if (p == FINGERPRINT_OK) {
    Serial.println("Deleted!");
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    Serial.println("Communication error");
  } else if (p == FINGERPRINT_BADLOCATION) {
    Serial.println("Could not delete in that location");
  } else if (p == FINGERPRINT_FLASHERR) {
    Serial.println("Error writing to flash");
  } else {
    Serial.print("Unknown error: 0x"); Serial.println(p, HEX);
  }
}
void scanFinger(void){
  uint8_t p;
  while(1){
    getFingerPrint(1);

    p = finger.fingerSearch();
    if (p == FINGERPRINT_OK) {
      Serial.println("Found a print match!");
      break;
    } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
      Serial.println("Communication error");
    } else if (p == FINGERPRINT_NOTFOUND) {
      Serial.println("Did not find a match");
    } else {
      Serial.println("Unknown error");
    }
  }
  Serial.print("Found ID #"); Serial.println(finger.fingerID);
  Serial.print("with confidence of "); Serial.println(finger.confidence);
}


void loop() {
  Serial.println("Enter choice: ");
  op = readNumber();
  Serial.println(op);
  switch(op){
    case 1:
      // add finger
      addFinger();
      break;
    case 2:
      // remove finger
      removeFinger();
      break;
    case 3:
      // scan for finger
      scanFinger();
      break;
  };
}
