
/* First created by JCasGen Fri Jan 03 10:37:15 CET 2014 */
package email.types;

import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.JCasRegistry;
import org.apache.uima.cas.impl.CASImpl;
import org.apache.uima.cas.impl.FSGenerator;
import org.apache.uima.cas.FeatureStructure;
import org.apache.uima.cas.impl.TypeImpl;
import org.apache.uima.cas.Type;
import org.apache.uima.cas.impl.FeatureImpl;
import org.apache.uima.cas.Feature;
import org.apache.uima.jcas.tcas.Annotation_Type;

/** 
 * Updated by JCasGen Fri Jan 03 10:37:16 CET 2014
 * @generated */
public class Message_Type extends Annotation_Type {
  /** @generated */
  @Override
  protected FSGenerator getFSGenerator() {return fsGenerator;}
  /** @generated */
  private final FSGenerator fsGenerator = 
    new FSGenerator() {
      public FeatureStructure createFS(int addr, CASImpl cas) {
  			 if (Message_Type.this.useExistingInstance) {
  			   // Return eq fs instance if already created
  		     FeatureStructure fs = Message_Type.this.jcas.getJfsFromCaddr(addr);
  		     if (null == fs) {
  		       fs = new Message(addr, Message_Type.this);
  			   Message_Type.this.jcas.putJfsFromCaddr(addr, fs);
  			   return fs;
  		     }
  		     return fs;
        } else return new Message(addr, Message_Type.this);
  	  }
    };
  /** @generated */
  @SuppressWarnings ("hiding")
  public final static int typeIndexID = Message.typeIndexID;
  /** @generated 
     @modifiable */
  @SuppressWarnings ("hiding")
  public final static boolean featOkTst = JCasRegistry.getFeatOkTst("email.Message");
 
  /** @generated */
  final Feature casFeat_from;
  /** @generated */
  final int     casFeatCode_from;
  /** @generated */ 
  public String getFrom(int addr) {
        if (featOkTst && casFeat_from == null)
      jcas.throwFeatMissing("from", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_from);
  }
  /** @generated */    
  public void setFrom(int addr, String v) {
        if (featOkTst && casFeat_from == null)
      jcas.throwFeatMissing("from", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_from, v);}
    
  
 
  /** @generated */
  final Feature casFeat_to;
  /** @generated */
  final int     casFeatCode_to;
  /** @generated */ 
  public String getTo(int addr) {
        if (featOkTst && casFeat_to == null)
      jcas.throwFeatMissing("to", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_to);
  }
  /** @generated */    
  public void setTo(int addr, String v) {
        if (featOkTst && casFeat_to == null)
      jcas.throwFeatMissing("to", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_to, v);}
    
  
 
  /** @generated */
  final Feature casFeat_date;
  /** @generated */
  final int     casFeatCode_date;
  /** @generated */ 
  public String getDate(int addr) {
        if (featOkTst && casFeat_date == null)
      jcas.throwFeatMissing("date", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_date);
  }
  /** @generated */    
  public void setDate(int addr, String v) {
        if (featOkTst && casFeat_date == null)
      jcas.throwFeatMissing("date", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_date, v);}
    
  
 
  /** @generated */
  final Feature casFeat_id;
  /** @generated */
  final int     casFeatCode_id;
  /** @generated */ 
  public String getId(int addr) {
        if (featOkTst && casFeat_id == null)
      jcas.throwFeatMissing("id", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_id);
  }
  /** @generated */    
  public void setId(int addr, String v) {
        if (featOkTst && casFeat_id == null)
      jcas.throwFeatMissing("id", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_id, v);}
    
  
 
  /** @generated */
  final Feature casFeat_subject;
  /** @generated */
  final int     casFeatCode_subject;
  /** @generated */ 
  public String getSubject(int addr) {
        if (featOkTst && casFeat_subject == null)
      jcas.throwFeatMissing("subject", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_subject);
  }
  /** @generated */    
  public void setSubject(int addr, String v) {
        if (featOkTst && casFeat_subject == null)
      jcas.throwFeatMissing("subject", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_subject, v);}
    
  
 
  /** @generated */
  final Feature casFeat_inReplyTo;
  /** @generated */
  final int     casFeatCode_inReplyTo;
  /** @generated */ 
  public String getInReplyTo(int addr) {
        if (featOkTst && casFeat_inReplyTo == null)
      jcas.throwFeatMissing("inReplyTo", "email.Message");
    return ll_cas.ll_getStringValue(addr, casFeatCode_inReplyTo);
  }
  /** @generated */    
  public void setInReplyTo(int addr, String v) {
        if (featOkTst && casFeat_inReplyTo == null)
      jcas.throwFeatMissing("inReplyTo", "email.Message");
    ll_cas.ll_setStringValue(addr, casFeatCode_inReplyTo, v);}
    
  



  /** initialize variables to correspond with Cas Type and Features
	* @generated */
  public Message_Type(JCas jcas, Type casType) {
    super(jcas, casType);
    casImpl.getFSClassRegistry().addGeneratorForType((TypeImpl)this.casType, getFSGenerator());

 
    casFeat_from = jcas.getRequiredFeatureDE(casType, "from", "uima.cas.String", featOkTst);
    casFeatCode_from  = (null == casFeat_from) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_from).getCode();

 
    casFeat_to = jcas.getRequiredFeatureDE(casType, "to", "uima.cas.String", featOkTst);
    casFeatCode_to  = (null == casFeat_to) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_to).getCode();

 
    casFeat_date = jcas.getRequiredFeatureDE(casType, "date", "uima.cas.String", featOkTst);
    casFeatCode_date  = (null == casFeat_date) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_date).getCode();

 
    casFeat_id = jcas.getRequiredFeatureDE(casType, "id", "uima.cas.String", featOkTst);
    casFeatCode_id  = (null == casFeat_id) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_id).getCode();

 
    casFeat_subject = jcas.getRequiredFeatureDE(casType, "subject", "uima.cas.String", featOkTst);
    casFeatCode_subject  = (null == casFeat_subject) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_subject).getCode();

 
    casFeat_inReplyTo = jcas.getRequiredFeatureDE(casType, "inReplyTo", "uima.cas.String", featOkTst);
    casFeatCode_inReplyTo  = (null == casFeat_inReplyTo) ? JCas.INVALID_FEATURE_CODE : ((FeatureImpl)casFeat_inReplyTo).getCode();

  }
}



    