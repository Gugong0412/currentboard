#ifndef DDI_PHASE22_R2_HW_H
#define DDI_PHASE22_R2_HW_H
#include <stdint.h>
#define DDI_DUT_SEQUENCE_APPROVED 0
#define DDI_VOLTAGE_SETTLING_QUALIFIED 0
#define DDI_LDO_INITIAL_TEST_GUARD_MS 100u /* provisional; NOT a max settling guarantee */
#define DDI_I2C_TIMINGR 0x10941723u
#define DDI_I2C2_SIDE1_CAP_PF_MAX 80u
#define DDI_TIMER_HZ 48000000u
#define DDI_TIM2_PSC 0u
#define DDI_TIM2_ARR 0xFFFFFFFFu
#define DDI_TIM2_CCMR1 0x0201u
#define DDI_TIM2_CCER 0x0031u
#define DDI_TIM2_DIER 0x0007u
typedef struct {const char *ref,*rail;uint8_t bus,address;double shunt_ohm,current_lsb_A;uint16_t adc_config,shunt_cal,sovl;} ddi_ina_channel_t;
static const ddi_ina_channel_t DDI_INA_CHANNELS[12] = {
 {"U700","VDDI_DIG",1,0x40u,20,1.5625e-08,0xAB28u,0x1000u,0x0190u},
 {"U710","VDDI",1,0x41u,20,1.5625e-08,0xABE8u,0x1000u,0x7FFFu},
 {"U720","VCI",1,0x42u,100,3.125e-09,0xABE8u,0x1000u,0x7FFFu},
 {"U730","AVDDH1",1,0x43u,3.01,1.038205980066445e-07,0xABE8u,0x1000u,0x7FFFu},
 {"U740","AVDDH2_S_O",1,0x44u,3.01,1.038205980066445e-07,0xABE8u,0x1000u,0x7FFFu},
 {"U750","VGH1",1,0x45u,3.01,1.038205980066445e-07,0xABE8u,0x1000u,0x7FFFu},
 {"U820","VGL1",2,0x40u,20,1.5625e-08,0xABE8u,0x1000u,0x7FFFu},
 {"U760","AVDDH2_GM",1,0x46u,3.01,1.038205980066445e-07,0xABE8u,0x1000u,0x7FFFu},
 {"U770","VGH2",1,0x47u,3.01,1.038205980066445e-07,0xABE8u,0x1000u,0x7FFFu},
 {"U780","VDDI_LPDP",1,0x48u,20,1.5625e-08,0xABE8u,0x1000u,0x7FFFu},
 {"U790","VDDI_OSC",1,0x49u,20,1.5625e-08,0xABE8u,0x1000u,0x7FFFu},
 {"U840","VGL2",2,0x41u,20,1.5625e-08,0xABE8u,0x1000u,0x7FFFu},
};
/* ADC signed20bit extreme/98% guard => possible clipping / invalid measurement; NOT hardware protection. */
static inline int32_t ddi_decode_signed20(uint32_t raw24){ uint32_t v=(raw24>>4)&0xFFFFFu; if(v&0x80000u)v|=0xFFF00000u;return (int32_t)v;}
static inline int ddi_possible_clipping(int32_t signed20){return signed20>=513802 || signed20<=-513802;}
/* MATHOF is arithmetic overflow; do not use it as sole ADC clipping detector. */
#endif
