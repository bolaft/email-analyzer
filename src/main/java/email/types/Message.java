

/* First created by JCasGen Fri Jan 03 10:37:15 CET 2014 */
package email.types;

import org.apache.uima.jcas.JCas; 
import org.apache.uima.jcas.JCasRegistry;
import org.apache.uima.jcas.cas.TOP_Type;

import org.apache.uima.jcas.tcas.Annotation;


/** 
 * Updated by JCasGen Fri Jan 03 10:37:16 CET 2014
 * XML source: /media/ext4/workspace/email-segmenter/src/main/resources/common/types/CommonTS.xml
 * @generated */
public class Message extends Annotation {
  /** @generated
   * @ordered 
   */
  @SuppressWarnings ("hiding")
  public final static int typeIndexID = JCasRegistry.register(Message.class);
  /** @generated
   * @ordered 
   */
  @SuppressWarnings ("hiding")
  public final static int type = typeIndexID;
  /** @generated  */
  @Override
  public              int getTypeIndexID() {return typeIndexID;}
 
  /** Never called.  Disable default constructor
   * @generated */
  protected Message() {/* intentionally empty block */}
    
  /** Internal - constructor used by generator 
   * @generated */
  public Message(int addr, TOP_Type type) {
    super(addr, type);
    readObject();
  }
  
  /** @generated */
  public Message(JCas jcas) {
    super(jcas);
    readObject();   
  } 

  /** @generated */  
  public Message(JCas jcas, int begin, int end) {
    super(jcas);
    setBegin(begin);
    setEnd(end);
    readObject();
  }   

  /** <!-- begin-user-doc -->
    * Write your own initialization here
    * <!-- end-user-doc -->
  @generated modifiable */
  private void readObject() {/*default - does nothing empty block */}
     
 
    
  //*--------------*
  //* Feature: from

  /** getter for from - gets 
   * @generated */
  public String getFrom() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_from == null)
      jcasType.jcas.throwFeatMissing("from", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_from);}
    
  /** setter for from - sets  
   * @generated */
  public void setFrom(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_from == null)
      jcasType.jcas.throwFeatMissing("from", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_from, v);}    
   
    
  //*--------------*
  //* Feature: to

  /** getter for to - gets 
   * @generated */
  public String getTo() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_to == null)
      jcasType.jcas.throwFeatMissing("to", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_to);}
    
  /** setter for to - sets  
   * @generated */
  public void setTo(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_to == null)
      jcasType.jcas.throwFeatMissing("to", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_to, v);}    
   
    
  //*--------------*
  //* Feature: date

  /** getter for date - gets 
   * @generated */
  public String getDate() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_date == null)
      jcasType.jcas.throwFeatMissing("date", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_date);}
    
  /** setter for date - sets  
   * @generated */
  public void setDate(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_date == null)
      jcasType.jcas.throwFeatMissing("date", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_date, v);}    
   
    
  //*--------------*
  //* Feature: id

  /** getter for id - gets 
   * @generated */
  public String getId() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_id == null)
      jcasType.jcas.throwFeatMissing("id", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_id);}
    
  /** setter for id - sets  
   * @generated */
  public void setId(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_id == null)
      jcasType.jcas.throwFeatMissing("id", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_id, v);}    
   
    
  //*--------------*
  //* Feature: subject

  /** getter for subject - gets 
   * @generated */
  public String getSubject() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_subject == null)
      jcasType.jcas.throwFeatMissing("subject", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_subject);}
    
  /** setter for subject - sets  
   * @generated */
  public void setSubject(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_subject == null)
      jcasType.jcas.throwFeatMissing("subject", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_subject, v);}    
   
    
  //*--------------*
  //* Feature: inReplyTo

  /** getter for inReplyTo - gets 
   * @generated */
  public String getInReplyTo() {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_inReplyTo == null)
      jcasType.jcas.throwFeatMissing("inReplyTo", "email.Message");
    return jcasType.ll_cas.ll_getStringValue(addr, ((Message_Type)jcasType).casFeatCode_inReplyTo);}
    
  /** setter for inReplyTo - sets  
   * @generated */
  public void setInReplyTo(String v) {
    if (Message_Type.featOkTst && ((Message_Type)jcasType).casFeat_inReplyTo == null)
      jcasType.jcas.throwFeatMissing("inReplyTo", "email.Message");
    jcasType.ll_cas.ll_setStringValue(addr, ((Message_Type)jcasType).casFeatCode_inReplyTo, v);}    
  }

    