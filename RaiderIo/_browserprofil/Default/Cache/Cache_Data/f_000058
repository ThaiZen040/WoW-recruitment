//sovrn beacon standalone .js
// 2025-06-06
window.sovrn = window.sovrn || {};
sovrn.auction = sovrn.auction || {};
let beaconFlag = false;
let cmpVersion = 0;

sovrn.auction = {
    doNotTrack: function (nav, win) {
        nav = nav || navigator;
        win = win || window;
        var optOutCookie = sovrn.auction.readCookie('tracking_optout');
        return nav.doNotTrack === 'yes'
                || nav.doNotTrack === '1'
                || nav.msDoNotTrack === '1'
                || win.doNotTrack === '1'
                || optOutCookie === '1';
    },

    readCookie: function (name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    },

    sendBeacon: function () {
        sovrn.auction.beaconConfig = sovrn.auction.getParams(sovrn.auction.getScriptTag());
        try {
            var id, beacon_frame, config;
            //Don't fire the beacon if it has already been fired
            if (beaconFlag) {
                return false;
            }
            id = 'sovrn_beacon';//this ends up being the iframe id for the beacon so could be anything not necessarily tied to a zone id
            beacon_frame = sovrn.auction.createiFrame(id, 1, 1);
            beacon_frame.src = sovrn.auction.getBeaconURL();
            document.body.appendChild(beacon_frame);
            beaconFlag = true;
        } catch (e) {
            return false;
        }
        return true;
    },

    getParams: function (currentScript) {
        var currentTagID = currentScript.getAttribute("id");
        var currentTag = document.getElementById(currentTagID);
        if (currentTag == null) {
            return false;
        }
        currentTagSRC = currentTag.src;
        //snag params from script_tags
        var query_string, qs_obj;
        qs_obj = {};
        query_string = currentTagSRC.split('?')[1] || '';
        query_string = query_string.split('#')[0] || ''; //Deal with hashes
        if (!query_string) return {};

        query_string.replace(
            new RegExp("([^?=&]+)(=([^&]*))?", "g"),
            function ($0, $1, $2, $3) {
                try {
                    qs_obj[$1] = decodeURIComponent($3);
                } catch (e) {
                    sovrn.ads.dbg(e);
                }
            }
        );
        qs_obj.currentTag = currentTagID;
        qs_obj.location = currentTag.parentNode.nodeName;
        return qs_obj;
        //
    },

    getScriptTag: function () {
        var tag_regex = /^(https?:)?\/\/.*\.lijit\.(com|dev)\/www\/sovrn_beacon_standalone\/sovrn_standalone_beacon(\.min)?\.js/i;
        //var tag_regex = /^(https?:)?\/\/.*\.lijit\.(com|dev)\/www\/delivery\/sovrn_stndalne_beacon(\.min)?\.js/i;
        var script_tags, i, cur_script,
            script_pattern = tag_regex;
        if ('currentScript' in document) {
            cur_script = document.currentScript;
            if (cur_script && script_pattern.test(cur_script.src)) {
                return cur_script;
            }
        }

        //Start from the last tag on the page and work backwards
        script_tags = document.getElementsByTagName('script');
        for (i = script_tags.length - 1; i >= 0; i--) {
            if (script_pattern.test(script_tags[i].src)) {
                return script_tags[i];
            }
        }
        return null;
    },
//
    createiFrame: function (id, w, h) {
        var ifr, iframe_style, i, j, attr, styles;
        ifr = document.createElement('iframe');
        iframe_style = ifr.style;

        attr = {
            id: id,
            margin: '0',
            padding: '0',
            frameborder: '0',
            width: w + '',
            height: h + '',
            scrolling: 'no',
            src: 'about:blank'
        };

        styles = {
            margin: '0px',
            padding: '0px',
            border: '0px none',
            width: w + 'px',
            height: h + 'px',
            overflow: 'hidden'
        };

        //Loop through the iframe attributes and set them
        for (i in attr) {
            if (attr.hasOwnProperty(i)) {
                ifr.setAttribute(i, attr[i]);
            }
        }

        //Loop through all the styles and apply them
        for (j in styles) {
            if (styles.hasOwnProperty(j)) {
                try {
                    iframe_style[j] = styles[j];
                } catch (e) {
                }
            }
        }

        return ifr;
    },//end create Iframe

    getBeaconURL: function () {

        var informerId = (sovrn.auction.beaconConfig.hasOwnProperty("iid")) ? sovrn.auction.beaconConfig.iid : "",
            gdprConsentString = sovrn.auction.gdprConsent || "",
            ccpaConsentString = sovrn.auction.ccpaConsent || "",
            gppConsentString = sovrn.auction.gppConsent || "",
            gppSidString = sovrn.auction.gppSid || "",
            gdprFlag = sovrn.auction.gdprApplies;

        return 'https://ce.lijit.com/beacon?informer=' + informerId
            + '&gdpr=' + (gdprFlag === null || gdprFlag === undefined ? '' : (gdprFlag ? '1' : '0'))
            + '&gdpr_consent=' + gdprConsentString
            + '&us_privacy=' + ccpaConsentString
            + '&gpp=' + gppConsentString
            + '&gpp_sid=' + gppSidString;
    },

    sovrnReady: function (f) {
        /in/.test(document.readyState) ? setTimeout(function () {sovrn.auction.sovrnReady(f)}, 50) : f()
    },

  configureConsents: function() {
    const _this = this;

    _this.lookupIabConsent(
        function(cmpResponse) {
          if (cmpVersion === 1) {
            // TCF v1 does not include a gdprApplies flag
            sovrn.auction.gdprConsent = cmpResponse.getConsentData.consentData;
            sovrn.auction.gdprApplies = null;
          } else {
            // TCF v2 returns the gdprApplies flag
            sovrn.auction.gdprConsent = cmpResponse.tcString;
            sovrn.auction.gdprApplies = cmpResponse.gdprApplies;
          }
          _this.configureCcpa();
        },
        function(e) {
          _this.configureCcpa();
        });

  },

  configureCcpa: function() {
    const _this = this;

    this.lookupCcpaConsent(
        function(apiResponse) {
          sovrn.auction.ccpaConsent = apiResponse.uspData;
          _this.configureGpp();
        },

        // ignoring errors for now - may want them to be tracked later
        function(e) {
          _this.configureGpp();
        })
  },

  configureGpp: function () {
    const _this = this;

    this.lookupIabConsentForGpp(
        function (apiResponse) {
          sovrn.auction.gppConsent = apiResponse.gppString;
          sovrn.auction.gppSid = apiResponse.applicableSections;
          _this.sendBeacon();
        },

        function (e) {
          _this.sendBeacon();
        })
  },

  callCmpFromSafeframe: function(commandName, dataName, callback, errorCallback) {
    const sfCallback = function(msgName, data) {
      if (msgName === 'cmpReturn') {
        callback(data[dataName]);
      } else {
        errorCallback()
      }
    };

    window.$sf.ext.register(1, 1, sfCallback);
    window.$sf.ext.cmp(commandName);
  },

  cmpCallbacks: {},

  // Taken mostly from example from
  // Quantcast's CMP JS API Spec pdf
  // And from Prebid consent management module
  callCmpWhileInIframe: function(commandName, cmpFrame, callbackFunc, errorCallback) {
    const apiName = (cmpVersion === 2) ? '__tcfapi' : '__cmp';

    const callId = Math.random().toString();
    const callName = `${apiName}Call`;
    const msg = {
      [callName]: {
        command: commandName,
        parameter: null,
        callId: callId
      }
    };
    if (cmpVersion !== 1) {
      msg[callName].version = cmpVersion;
      }

    sovrn.auction.cmpCallbacks[callId] = callbackFunc;
    cmpFrame.postMessage(msg, '*');

    /** when we get the return message, call the stashed callback */
    window.addEventListener('message', readPostMessageResponse, false);

    function readPostMessageResponse(event) {

      const cmpDataPkgName = `${apiName}Return`;
      let json = {};

      try {
        json = typeof event.data === 'string' ? JSON.parse(event.data) :
            event.data;
      } catch (ignore) {}
      if (json[cmpDataPkgName] && json[cmpDataPkgName].callId) {
        const payload = json[cmpDataPkgName];
        if (typeof sovrn.auction.cmpCallbacks[payload.callId] === 'function') {
          sovrn.auction.cmpCallbacks[payload.callId](payload.returnValue,
              payload.success);
        } else {
          errorCallback('Callback must be function type.')
        }
      }
    }
  },

  /**
   * Find CMP if exists & read from it.
   *
   * @param cmpSuccess acts as a success callback when CMP returns a value
   * @param cmpError acts as an error callback, passes an error message
   */
  lookupIabConsent: function(cmpSuccess, cmpError) {
    function findCMP() {
      let f = window;
      let cmpFrame;
      let cmpFunction;
      while (!cmpFrame) {
        try {
          if (typeof f.__tcfapi === 'function' || typeof f.__cmp ===
              'function') {
            if (typeof f.__tcfapi === 'function') {
              cmpVersion = 2;
              cmpFunction = f.__tcfapi;
            } else {
              cmpVersion = 1;
              cmpFunction = f.__cmp;
            }
            cmpFrame = f;
            break;
          }
        } catch (e) {}

        // need separate try/catch blocks due to the exception errors thrown when trying to check for a frame that doesn't exist in 3rd party env
        try {
          if (f.frames['__tcfapiLocator']) {
            cmpVersion = 2;
            cmpFrame = f;
            break;
          }
        } catch (e) {}

        try {
          if (f.frames['__cmpLocator']) {
            cmpVersion = 1;
            cmpFrame = f;
            break;
          }
        } catch (e) {}

        if (f === window.top) {
          break;
        }
        f = f.parent;
      }
      return {
        cmpFrame,
        cmpFunction
      };
    }

    function v2CmpResponseCallback(tcfData, success) {
      if (success && typeof tcfData.tcString === "string") {
        if (tcfData.eventStatus === 'tcloaded' || tcfData.eventStatus ===
            'useractioncomplete') {
          cmpSuccess(tcfData);
        } else if (tcfData.eventStatus === 'cmpuishown' &&
            tcfData.tcString.length > 0 && tcfData.purposeOneTreatment ===
            true) {
          cmpSuccess(tcfData);
        } else {
          cmpError('Consent string is not available.');
        }
      } else {
        cmpError(
            'CMP unable to register callback function.  Please check CMP setup.');
      }
    }

    function handleV1CmpResponseCallbacks() {
      const cmpResponse = {};

      function afterEach() {
        if (cmpResponse.getConsentData && cmpResponse.getVendorConsents) {
          cmpSuccess(cmpResponse);
        } else if (cmpResponse.hasOwnProperty('getConsentData') && cmpResponse.hasOwnProperty('getVendorConsents') &&
            (!cmpResponse.getConsentData || !cmpResponse.getVendorConsents)) {
          cmpError('Consent string is blank.');
        }
      }

      return {
        consentDataCallback: function(consentResponse) {
          cmpResponse.getConsentData = consentResponse;
          afterEach();
        },
        vendorConsentsCallback: function(consentResponse) {
          cmpResponse.getVendorConsents = consentResponse;
          afterEach();
        }
      }
    }

    const v1CallbackHandler = handleV1CmpResponseCallbacks();
    const {
      cmpFrame,
      cmpFunction
    } = findCMP();

    if (!cmpFrame) {
      return cmpError('CMP not found.');
    }

    if (typeof cmpFunction === 'function') {
      if (cmpVersion === 1) {
        cmpFunction('getConsentData', null,
            v1CallbackHandler.consentDataCallback);
        cmpFunction('getVendorConsents', null,
            v1CallbackHandler.vendorConsentsCallback);
      } else if (cmpVersion === 2) {
        cmpFunction('addEventListener', cmpVersion, v2CmpResponseCallback);
      }
    } else if (cmpVersion === 1 && !!(window.$sf && window.$sf.ext) &&
        typeof window.$sf.ext.cmp ===
        'function') {
      // this safeframe workflow is only supported with TCF v1 spec; the v2 recommends to use the iframe postMessage route instead
      // (even if you are in a safeframe).
      this.callCmpFromSafeframe('getConsentData',
          v1CallbackHandler.consentDataCallback, cmpError);
      this.callCmpFromSafeframe('getVendorConsents',
          v1CallbackHandler.vendorConsentsCallback, cmpError);
    } else {
      if (cmpVersion === 1) {
        this.callCmpWhileInIframe('getConsentData', cmpFrame,
            v1CallbackHandler.consentDataCallback, cmpError);
        this.callCmpWhileInIframe('getVendorConsents', cmpFrame,
            v1CallbackHandler.vendorConsentsCallback, cmpError);
      } else if (cmpVersion === 2) {
        this.callCmpWhileInIframe('addEventListener', cmpFrame,
            v2CmpResponseCallback, cmpError);
      }
    }
  },

  /**
   * Find CCPA API if it exists and query it
   *
   * @param apiSuccess acts as a success callback when CMP returns a value
   * @param apiError acts as an error callback, passes an error message
   */
  lookupCcpaConsent: function(apiSuccess, apiError) {
    var _this = this,
        apiFunction,
        apiCommand = 'getUSPData',
        apiVersion = 1,
        apiResponse = {
          uspData: '',
          success: false
        },

        apiCallback = function(uspData, success) {
          apiResponse.uspData = uspData && uspData.uspString || "";
          apiResponse.success = success;

          if (success) {
            apiSuccess(apiResponse);
          } else {
            apiError();
          }
        };

    try {
      apiFunction = window.__uspapi || window.top.__uspapi;
    } catch (e) {
      apiError(e)
    }

    if (typeof apiFunction  === 'function') {
      apiFunction(apiCommand, apiVersion, apiCallback);
    } else {
      // Assuming safeframes with no api proxy, or child iframe
      var f = window, apiFrame, uniqueId = (new Date()).getTime();

      while (!apiFrame) {
        try {
          if (f.frames['__uspapiLocator']) {
            apiFrame = f;
          }
        } catch (e) {
          apiError(e);
          return;
        }

        if (f === window.top) {
          apiError();
          return;
        }

        f = f.parent;
      }

      // Found frame to post a message to
      var messageToApiWindow = {
        __uspapiCall: {
          command: apiCommand,
          version: apiVersion,
          parameter: null,
          callId: uniqueId
        }
      };
      apiFrame.postMessage(messageToApiWindow, '*');

      // Event handler for response
      window.addEventListener("message", function(event) {
        if (event.data && event.data.__uspapiReturn && (event.data.__uspapiReturn.callId === uniqueId)) {
          if (event.data.__uspapiReturn.success) {
            apiSuccess(event.data.__uspapiReturn.returnValue)
          } else {
            apiError()
          }
        }
      }, false);
    }
  },


  cmpClient: function (
    {
      apiName,
      apiVersion,
      apiArgs = ['command', 'callback', 'parameter', 'version'],
      callbackArgs = ['returnValue', 'success'],
    },
    win = window
  ){
    const cmpCallbacks = {};
    const callName = `${apiName}Call`;
    const cmpDataPkgName = `${apiName}Return`;

    function handleMessage(event) {
      const json = (typeof event.data === 'string' && event.data.includes(cmpDataPkgName)) ? JSON.parse(event.data) : event.data;
        if (json?.[cmpDataPkgName]?.callId) {
          const payload = json[cmpDataPkgName];

            if (cmpCallbacks.hasOwnProperty(payload.callId)) {
                    cmpCallbacks[payload.callId](...callbackArgs.map(name => payload[name]));
            }
        }
    }

    function findCMP() {
      let f = win;
      let cmpFrame;
      let isDirect = false;
      while (f != null) {
        try {
          if (typeof f[apiName] === 'function') {
            cmpFrame = f;
            isDirect = true;
            break;
          }
        } catch (e) {}

        // need separate try/catch blocks due to the exception errors thrown when trying to check for a frame that doesn't exist in 3rd party env
        try {
          if (f.frames[`${apiName}Locator`]) {
            cmpFrame = f;
            break;
          }
        } catch (e) {}

        if (f === win.top) break;
          f = f.parent;
      }

      return [
        cmpFrame,
        isDirect
      ];
    }

    const [cmpFrame, isDirect] = findCMP();

    if (!cmpFrame) {
      return;
    }

    function resolveParams(params) {
      params = Object.assign({version: apiVersion}, params);
      return apiArgs.map(arg => [arg, params[arg]])
    }

    function wrapCallback(callback, resolve, reject, preamble) {
      return function (result, success) {
        preamble && preamble();
        const resolver = success == null || success ? resolve : reject;
        if (typeof callback === 'function') {
          resolver();
          return callback.apply(this, arguments);
        } else {
          resolver(result);
        }
      }
    }

    let client;

    if (isDirect) {
      client = function invokeCMPDirect(params = {}) {
        return new Promise((resolve, reject) => {
          const ret = cmpFrame[apiName](...resolveParams({
                        ...params,
                        callback: params.callback && wrapCallback(params.callback, resolve, reject)
          }).map(([_, val]) => val));
          if (params.callback == null) {
            resolve(ret);
          }
        });
      };
    } else {
      win.addEventListener('message', handleMessage, false);

      client = function invokeCMPFrame(params) {
        return new Promise((resolve, reject) => {
          // call CMP via postMessage
          const callId = Math.random().toString();
          const msg = {
            [callName]: {
              ...Object.fromEntries(resolveParams(params).filter(([param]) => param !== 'callback')),
              callId: callId
            }
          };

          cmpCallbacks[callId] = wrapCallback(params?.callback, resolve, reject, params?.callback == null && (() => {
                        delete cmpCallbacks[callId]
          }));
          cmpFrame.postMessage(msg, '*');
        });
      };
    }
    client.isDirect = isDirect;
    return client;
  },

  lookupIabConsentForGpp: function (onSuccess, onError) {
    const _this = this;
    const cmp = _this.cmpClient({
      apiName: '__gpp',
      apiVersion: 1,
    });
    if (!cmp) {
      return onError('GPP CMP not found.');
    }

    cmp({
      command: 'addEventListener',
        callback: function (evt) {
          if (evt) {
            if (evt.eventName === 'sectionChange' || evt.pingData.cmpStatus === 'loaded') {
              cmp({command: 'getGPPData'}).then((gppData) => {
                return Promise.all(
                  (gppData?.pingData?.supportedAPIs || [])
                    .map((name) => cmp({command: 'getSection', parameter: name})
                      .catch(() => {})
                      .then((res) => [name, res]))
                  ).then((sections) => {
                    const sectionData = Object.fromEntries(sections.filter(([_, val]) => val != null));
                    processCmpData({gppData, sectionData}, {onSuccess, onError});
                  })
              });
            } else if (evt.pingData.cmpStatus === 'error') {
              onError('CMP returned with a cmpStatus:error response.  Check CMP setup.');
            }
          }
        }
    });

    function processCmpData(consentData, {onSuccess, onError}) {
      function checkData() {
        const gppString = consentData?.gppData?.gppString;
        const gppSection = consentData?.gppData?.applicableSections;

        return !!(
          (!Array.isArray(gppSection)) ||
          (Array.isArray(gppSection) && (!gppString || !isStr(gppString)))
        );
        }

        if (checkData()) {
          onError(`CMP returned unexpected value during lookup process.`, consentData);
        } else {
          onSuccess(storeConsentData(consentData));
        }
    }

    function storeConsentData({gppData, sectionData} = {}) {
      let consentData = {
        gppString: (gppData) ? gppData.gppString : undefined,
        gppData: (gppData) || undefined,
      };
      consentData.applicableSections = applicableSections(gppData);
      consentData.apiVersion = 1;
      consentData.sectionData = sectionData;
      return consentData;
    }

    function applicableSections(gppData) {
      return gppData && Array.isArray(gppData.applicableSections) && gppData.applicableSections.length > 0 && gppData.applicableSections[0] !== 0
        ? gppData.applicableSections
        : [];
    }

    function isStr(object){
      return Object.prototype.toString.call(object) === '[object ' + 'String' + ']';
    }
  }

};

sovrn.auction.sovrnReady(function () {
    let dnt = sovrn.auction.doNotTrack();
    if (dnt === false) {
        sovrn.auction.configureConsents();
    }
});
